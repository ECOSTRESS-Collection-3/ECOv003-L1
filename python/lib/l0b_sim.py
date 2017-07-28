import numpy as np
import h5py
import subprocess
import ctypes
#from .misc import time_split, ecostress_file_name
from .write_standard_metadata import WriteStandardMetadata
import os
from datetime import datetime
from geocal import Time

# import pkt_defs.py

J2KS=946728000.0   # seconds from UNIX EPOCH to J2000 EPOCH 2000-01-01:12:00:00
GPSS=315964800.0   # seconds from UNIX EPOCH to GPS EPOCH 1980-01-06:00:00:00
GP2K = J2KS - GPSS # difference

'''
New L0B contents

"flex/bip": shape (203, 64, 256, 6), type "<i2">
"flex/id_line": shape (203, 64), type "<u4">
"flex/id_packet": shape (203,), type "<u4">
"flex/state": shape (203,), type "<u4">
"flex/time_fsw": shape (203,), type "<f8">
"flex/time_sync_fpie": shape (203,), type "<u8">
"flex/time_sync_fsw": shape (203,), type "<u8">

By seconds:

"hk/bad/hr/attitude": shape (479, 4), type "<f4">
"hk/bad/hr/position": shape (479, 3), type "<f4">
"hk/bad/hr/time": shape (479,), type "<f8">
"hk/bad/hr/time_fsw": shape (479,), type "<f8">
"hk/bad/hr/velocity": shape (479, 3), type "<f4">

"hk/status/mode/dpuio": shape (479,), type "<u4">
"hk/status/mode/op": shape (479,), type "<u4">
"hk/status/motor/bb1": shape (479,), type "<u4">
"hk/status/motor/bb2": shape (479,), type "<u4">
"hk/status/motor/last/register": shape (479,), type "|u1">
"hk/status/motor/last/value": shape (479,), type "<u4">
"hk/status/motor/mode": shape (479,), type "<u4">
"hk/status/motor/position": shape (479, 5), type "<u4">
"hk/status/motor/pstate": shape (479,), type "|u1">
"hk/status/motor/rate": shape (479, 5), type "<u4">
"hk/status/motor/sun_safe": shape (479,), type "<u4">
"hk/status/motor/time": shape (479, 5), type "<f8">
"hk/status/motor/wait": shape (479,), type "|u1">
"hk/status/temperature": shape (479, 2, 5), type "<u2">
"hk/status/time": shape (479,), type "<f8">
"hk/status/time_fsw": shape (479,), type "<f8">

'''

# short word offsets into FPIE packet array

# packet primary header
HSYNC = 0
PKTID = HSYNC + 2
ENCOD = PKTID + 2
ISTATE = ENCOD + 128
FTIME = ISTATE + 2
DTIME = FTIME + 4
DSYNC = DTIME + 4
PLEN = DSYNC + 4

# compression header
f_n_m = 148
f_b_d = f_n_m + 2
f_n_x = f_b_d + 2
f_n_y = f_n_x + 2
f_n_z = f_n_y + 2
f_k_i = f_n_z + 2
f_c_s = f_k_i + 2

# comp init data
cb1 = 162
cb2 = cb1 + 20
cb3 = cb2 + 20
cb4 = cb3 + 20
cb5 = cb4 + 20
cb6 = cb5 + 20
HSUM = 282
HDR_LEN = 284

# uncompressed data block
DB1 = HDR_LEN
DB2 = DB1 + 16384
DB3 = DB2 + 16384
DB4 = DB3 + 16384
DB5 = DB4 + 16384
DB6 = DB5 + 16384
DSUM = DB6 + 16384

# total packet length in 16 bit words
PKT_LEN = DSUM + 2
BANDS = 6
# number of pixels per focal plane
PPFP = 256
# number of focal planes per full scan
FPPSC = 5400
# number of FPs in each BB per scan
BBLEN = 64
# Total FPs per scan including hot and cold BB
FPB3 = FPPSC + BBLEN*2
# number of FPs per raw packet
FPPPKT = 64
# Scans per scene
SCPS = 44
# standard packets per scene rounded up
PKTPS = int( (SCPS*FPB3+FPPPKT-1) / FPPPKT )

# FPIE mirror encoder - 50.95 degree swath width
# covered by 25.475 degree of mirror scan.  Mirror
# is 2-sided, so every other scan is 180 degrees apart
MAX_FPIE=1749248
CNT_DUR = (60/25.4)/float( MAX_FPIE )  # = 1.3504 microsecond
ANG_INC = 360.0 / float( MAX_FPIE )  # = 0.000205803 deg
PIX_ANG = 25.475 / float( FPPSC )  # = 0.004717592 deg
PIX_EV = PIX_ANG / ANG_INC # = 22.92289 counts/pix
# For now, if you change this number make sure to also change
# frame_time in EcostressTimeTable. Eventually that should go away,
# the time table should be reading this from the input data. But for
# now this is hardcoded.
#
# Short term, change this to match EcostressTimeTable pixel duration.
# We will want to change this back, but for now change this to match
# existing test data. See Issue #13 in github.
#PIX_DUR = 0.0000321982
PIX_DUR = 0.0000321875
PKT_DUR = PIX_DUR * float( FPPPKT )
# Black body pixels are BEFORE image pixels
ANG1 = 25.475 / 2.0
ANG0 = 0.0 - PIX_ANG * float( BBLEN*2.0 ) - ANG1

class L0BSimulate(object):
  # This is used to generate L0 simulated data. We take the output of the
  # l1a_raw pge and reverse the processing to produce a L0 file.
  def __init__(self, l1a_raw_att_fname, l1a_eng_fname, scene_files):
    # Create a L0Simulate to process the given files. The orbit based files
    # are passed in as a file name, and the scene based files are passed as a dict
    # with keys of scene id. The values in the dict are an array, the first entry
    # is the L1A_RAW_PIX file and the second is the L1A_BB file.
    self.l1a_eng_fname = l1a_eng_fname
    self.l1a_raw_att_fname = l1a_raw_att_fname
    self.scene_files = scene_files

  def hdf_copy(self, fname, group, group_out = None, scene = None):
    # Copy the given group from the give file to our output file.
    # Default it to give the output the same group name, but can change this.
    # If scene is passed in, we nest the output by "Scene_<num>"
    if(group_out is None):
      if(scene is not None):
        group_out = "/Data/Scene_%d%s" % (scene, group)
      else:
        group_out = "/Data" + group
    subprocess.run(["h5copy", "-i", fname, "-o", self.l0b_fname, "-p",
                    "-s", group, "-d", group_out], check=True)

  def create_file(self, l0b_fname):
    print("====  CREATE_FILE L0B_FNAME %s ====" % l0b_fname )
    print("ANG0=%f ANG1=%f PIX_ANG=%14.8e" % (ANG0, ANG1, PIX_ANG ))
    print("====  Start time  ", datetime.now(), "  ====")
    self.l0b_fname = l0b_fname
    l0b_fd = h5py.File(self.l0b_fname, "w", driver='core')

    # Write Standarad Metadata fake-out WriteStandardMetadata()
    m = WriteStandardMetadata(l0b_fd, product_specfic_group ="L0BMetadata",
        proc_lev_desc = 'Level 0B Data Parameters',
        pge_name="L0B",
        build_id="0.0", pge_version="0.0", level0_file=True )
    a = self.l0b_fname.split('_')
    b = a[2].split('T')
    m.set("RangeBeginningDate", b[0])
    m.set("RangeBeginningTime", b[1])
    b = a[3].split('T')
    m.set("RangeEndingDate", b[0])
    m.set("RangeEndingTime", b[1])
    m.write()
    l0b_fd.flush()

    # copy data from raw attitude/ephemeris file to HK packets
    att_fd = h5py.File(self.l1a_raw_att_fname, "r") 
    aq=att_fd["Attitude/quaternion"]
    aqc, aqr = aq.shape
    at=att_fd["Attitude/time_j2000"]
    ep=att_fd["Ephemeris/eci_position"]
    epc, epr = ep.shape
    ev=att_fd["Ephemeris/eci_velocity"]
    et=att_fd["Ephemeris/time_j2000"]

    # create ancillary data sets
    print("Creating HK Group")
    hk_g = l0b_fd.create_group("/hk")
    hb = l0b_fd.create_group("/hk/bad")

    hbh = l0b_fd.create_group("/hk/bad/hr")
    att = hbh.create_dataset("attitude", (aqc,4), dtype=np.float32)
    pos = hbh.create_dataset("position", (epc,3), dtype=np.float32)
    att_time = hbh.create_dataset("time", (aqc,), dtype=np.float64)
    att_fsw = hbh.create_dataset("time_fsw", (epc,), dtype=np.float64)
    vel = hbh.create_dataset("velocity", (epc,3), dtype=np.float32)

    hs = l0b_fd.create_group("/hk/status")
    hsmd = l0b_fd.create_group("/hk/status/mode")
    dp_hsmd = hsmd.create_dataset("dpuio", (aqc,), dtype=np.uint32)
    op_hsmd = hsmd.create_dataset("op", (aqc,), dtype=np.uint32)

    hsmt = l0b_fd.create_group("/hk/status/motor")
    bb1_hsmt = hsmt.create_dataset("bb1", (aqc,), dtype=np.uint32)
    bb2_hsmt = hsmt.create_dataset("bb2", (aqc,), dtype=np.uint32)

    hsmtl = l0b_fd.create_group("/hk/status/motor/last")
    rg_hsmtl = hsmtl.create_dataset("register", (aqc,), dtype=np.uint8)
    va_hsmtl = hsmtl.create_dataset("value", (aqc,), dtype=np.uint32)

    md_hsmt = hsmt.create_dataset("mode", (aqc,), dtype=np.uint32)
    po_hsmt = hsmt.create_dataset("position", (aqc,5), dtype=np.uint32)
    ps_hsmt = hsmt.create_dataset("pstate", (aqc,), dtype=np.uint8)
    rt_hsmt = hsmt.create_dataset("rate", (aqc,), dtype=np.uint32)
    ss_hsmt = hsmt.create_dataset("sun_safe", (aqc,), dtype=np.uint32)
    ti_hsmt = hsmt.create_dataset("time", (aqc,), dtype=np.float64)

    bbt = hs.create_dataset("temperature", (epc,2,5), dtype=np.uint16)
    bb_time = hs.create_dataset("time", (epc,), dtype=np.float64)
    bb_fsw = hs.create_dataset("time_fsw", (epc,), dtype=np.float64)

    # Copy ATT/EPH into HK data set
    att[:,:] = aq[:,:]
    pos[:,:] = ep[:,:]
    vel[:,:] = ev[:,:]
    for i in range( aqc ): att_time[i] = Time.time_j2000(at[i]).gps
    for i in range( epc ): att_fsw[i] = Time.time_j2000(et[i]).gps

    #  Copy RTD temps from ENG file
    l1e = h5py.File(self.l1a_eng_fname,"r")
    #  ****  convert Kelvin to DN  ****  just copy for now
    bbt[:,0:] = l1e["rtdBlackbodyGradients/RTD_295K"][:]
    bbt[:,1:] = l1e["rtdBlackbodyGradients/RTD_325K"][:]
    '''
    rtd = [j for j in range(2)]
    r = np.zeros( 5, dtype=np.float32 )
    j = 0
    for t in (295, 325):
      rtd[j] = l1e["/rtdBlackbodyGradients/RTD_%dK" % t]
      j += 1
    dim = len( rtd[0].shape )
    if dim == 1:  #  set all output BB temps to the same set
      for j in range(2):
        r[:] = rtd[j][:]
        bbt[:,j,:] = (65535/r.max())*r
    else:  #  assume the same number 
      for j in range(2):
        for i in range(rtd[j].shape[1]):
          r[:] = rtd[j][i,:]
          bbt[i,j,:] = (65535/r.max())*r
    '''
    bb_time[:] = att_time[:aqc]  # just copy times from ATT/EPH for now
    bb_fsw[:] = att_fsw[:epc]
    att_fd.close()
    l1e.close()
    l0b_fd.flush()

    # create FLEX packet
    flex_g = l0b_fd.create_group("/flex")
    # create packet dataset template
    bip = flex_g.create_dataset("bip", shape=(1,FPPPKT,PPFP,BANDS), maxshape=(None, FPPPKT,PPFP,BANDS), dtype='uint16' )
    lid = flex_g.create_dataset("id_line", shape=(1,FPPPKT), maxshape=(None,FPPPKT), dtype='uint32' )
    pid = flex_g.create_dataset("id_packet", shape=(1,), maxshape=(None,), dtype='uint32' )
    flex_st = flex_g.create_dataset("state", shape=(1,), maxshape=(None,), dtype='uint32' )
    fswt = flex_g.create_dataset("time_fsw", shape=(1,), maxshape=(None,), dtype='float64' )
    fpie_sync = flex_g.create_dataset("time_sync_fpie", shape=(1,), maxshape=(None,), dtype='uint64' )
    fsw_sync = flex_g.create_dataset("time_sync_fsw", shape=(1,), maxshape=(None,), dtype='uint64' )

    # running count of packets
    tot_pkt = 0
    # running count of image lines
    tot_lines = 0
    # *** packet ID adjust for missing packets ***
    pkt_id = 0

    # working array including PIX and BB, and 1 packet
    bufsiz = FPB3 + FPPPKT
    pix_buf = np.zeros( ( PPFP, bufsiz, BANDS ), dtype=np.uint16 )
    ev_buf = np.zeros( FPPPKT, dtype=np.uint32 )
    p0 = 0
    prev = 0
    pix_dat = [b for b in range(BANDS)]
    b295 = [b for b in range(BANDS)]
    b325 = [b for b in range(BANDS)]
    angnadir = 180.0

    # process scenes make sure to do it in order
    total_scenes = len(self.scene_files)
    mangle = ANG0
    for v, scn in enumerate(self.scene_files):
      scene, l1a_raw_pix_fname, l1a_bb_fname, onum, tstart, tend = scn

      # open raw pixel data file
      pix_fd = h5py.File(l1a_raw_pix_fname, "r", driver='core')

      # Also get simulated black body data
      bb_fd = h5py.File(l1a_bb_fname, "r", driver='core')

      # link to pixel and bb datsasets
      for b in range( BANDS ):
        pix_dat[b] = pix_fd["/UncalibratedPixels/pixel_data_%d" %(b+1)]
        b295[b] = bb_fd["/BlackBodyPixels/B%d_blackbody_295K" % (b+1)]
        b325[b] = bb_fd["/BlackBodyPixels/B%d_blackbody_325K" % (b+1)]

      pix_2k=pix_fd["/Time/line_start_time_j2000"]

      # lines and pix per scene (assume all BANDS are the same)
      lines, pix = pix_dat[0].shape
      tot_lines = tot_lines + lines
      line = 0
      # pkts for scene
      tot_pkt = int( ( FPB3*tot_lines/PPFP + FPPPKT -1 ) / FPPPKT )
      # extend packet dataset to new total
      bip.resize( tot_pkt, 0 )
      lid.resize( tot_pkt, 0 )
      pid.resize( tot_pkt, 0 )
      flex_st.resize( tot_pkt, 0 )
      fswt.resize( tot_pkt, 0 )
      fpie_sync.resize( tot_pkt, 0 )
      fsw_sync.resize( tot_pkt, 0 )
      print("\n===  SCENE=%d %s TOTAL=%d P0=%d tot_lines=%d tot_pkt=%d" % (v, l1a_raw_pix_fname, total_scenes, p0, tot_lines, tot_pkt))

      # Iterate through data lines in current scene 256 lines at a time
      while line < lines:

        # copy pix and BB data to buffer at pkt offset
        # 2017-02-16 - BBs come before pix data
        ps2 = p0; pe2 = ps2 + BBLEN
        ps3 = pe2; pe3 = ps3 + BBLEN
        ps1 = pe3; pe1 = ps1 + FPPSC

        # assemble pix and bb data into buffer, with offset from previous buffer
        for b in range( BANDS ):
    #  Band interleaved by pixels (BANDS*FPPSC, PPFP)
          pix_buf[:,ps1:pe1,b] = pix_dat[b][line:line+PPFP,:]
          pix_buf[:,ps2:pe2,b] = b295[b][line:line+PPFP,:]
          pix_buf[:,ps3:pe3,b] = b325[b][line:line+PPFP,:]

        # step through buffer in packet steps (FPPPKT) starting from 0
        bts = 0
        bte = p0 + FPB3
        t2k = pix_2k[line] - PIX_DUR*float(BBLEN*2.0+p0) # offset for BB pixels
        angnadir = 180.0 - angnadir
        print("====  ", datetime.now(), "  ====")
        print("L=%d PKT=%d T2K=%f P2K=%f ANG=%f NADIR=%3.1f BTE=%d P0=%d PS1=%d PS2=%d PS3=%d PE3=%d" %(line,pkt_id,t2k,pix_2k[line],mangle,angnadir,bte,p0,ps1,ps2,ps3,pe3))
        while bts < bte:

          # see where current buffer pointer is
          pe1 = bts + FPPPKT
          #print("SCENE=%s PKT_ID=%d MANGLE=%f BTS=%d BTE=%d" %(scene, pkt_id, mangle, bts, bte))
          # write a packet if sufficient data
          if pe1 <= bte:

            # write next packet ancillary data
            pid[pkt_id] = pkt_id+1
            fswt[pkt_id] = Time.time_j2000(t2k).gps
            print("SCENE=%s Pkt %d T2k=%f BTS=%d BTE=%d MANGLE=%f PREV=%d" %(scene, pkt_id, t2k, bts, bte, mangle, prev))
            # *** generate ENCODer values from -2*BB -12.738 to +12.738
            # *** add FPIE sync clock and FPIE 1st pix to FSWT offset (1MHz)
            for i in range(0,FPPPKT):
              if i >= prev:
                angle = mangle + angnadir  # use current NADIR angle
              else:
                angle = mangle + 180 - angnadir  # use previous NADIR angle
              if angle >= 0.0: ev_buf[i] = int( ( angle ) / ANG_INC )
              else: ev_buf[i] = int( ( angle+360.0 ) / ANG_INC )
              mangle = mangle + PIX_ANG
              if mangle >= ANG1: mangle = ANG0

            # write packet data
            lid[pkt_id,:] = ev_buf[:]
            for b in range(BANDS):
              bip[pkt_id,:,:,b] = pix_buf[:,bts:pe1,b].transpose()
            # next point in pix_buf
            bts = pe1
            # next packet
            pkt_id += 1
            t2k += PKT_DUR
            prev = 0

            if bts == bte: # reached end of valid data in current pix_buf
              # reset offset into next pix_buf
              p0 = 0
              print("End PIX_BUF SCENE=%d BTS=%d PKT_ID=%d ANG=%f" %(v,bts,pkt_id,mangle))

          else: # at the remainder of current pix_buf
            print("Remainder SCENE=%d BTE=%d BTS=%d PKT_ID=%d ANG=%f" % (v,bte, bts,pkt_id,mangle))

            # set offset to next pix_buf
            p0 = bte - bts
            prev = p0
            # move remainder data to front of pix_buf
    #  Band interleaved by pixels (BANDS*FPPSC, PPFP)
            pix_buf[:,:p0,:] = pix_buf[:,bts:bte,:]
            # escape bts while loop to go to next scene
            if v+1 < total_scenes or line+PPFP < lines:
              bts = bte
            else: # last runt packet of last scene< fill remaining with dummy
              bts = 0
              bte = FPPPKT
              print("Final runt packet: %d" % p0 )
              pix_buf[ 0:PPFP, p0:FPPPKT, :] = 0
          # end writing current packet

        # next line in scene
        line += PPFP
        # end copying current pix_buf to packets

      # close current raw pix and bb files
      pix_fd.close()
      bb_fd.close()
      l0b_fd.flush()
      # end writing packets for current scene file
    # *** take care of runt packet of last scene ***
    print("End all scenes, TOT_LINES=%d runt P0=%d" % (tot_lines, p0) )
    # end scene files loop

    # Write L0B metadata
    print("Writing L0BMetadata to L0B file %s" % self.l0b_fname )
    l0b_mg = l0b_fd["L0BMetadata"]
    #l0b_pl = l0b_mg.create_dataset("PacketList", shape=(tot_pkt,), dtype="uint32")
    #l0b_ps = l0b_mg.create_dataset("PacketStatus", shape=(tot_pkt,), dtype="uint16")
    #for i in range( tot_pkt ): l0b_pl[i] = i
    #l0b_ps[:] = 0
    #l0b_ps.attrs["PacketPercentage"] = "1.00000000"
    st = h5py.special_dtype(vlen=str)
    l0b_ifl = l0b_mg.create_dataset("InputFileList", shape=(len(2*self.scene_files),), dtype=st)
    for v in range(len( self.scene_files )):
      l0b_ifl[v*2] = self.scene_files[v][1]
      l0b_ifl[v*2+1] = self.scene_files[v][2]
    l0b_fd.flush()

    # done...close L0B file
    l0b_fd.close()
    print("====  End time  ", datetime.now(), "  ====")
