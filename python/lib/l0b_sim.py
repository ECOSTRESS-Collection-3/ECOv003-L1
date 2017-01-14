import numpy as np
import h5py
import subprocess
import ctypes
#from .misc import time_split, ecostress_file_name
from .write_standard_metadata import WriteStandardMetadata
import os
from datetime import datetime
# import pkt_defs.py

# short word offsets into FPIE packet array

# packet primary header
HSYNC = 0
PCNT = HSYNC + 2
ENCOD = PCNT + 2
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
ANG_INC = 360.0 / float( MAX_FPIE )
PIX_ANG = 25.475 / float( FPPSC )
PIX_EV = int( PIX_ANG / ANG_INC )
ANG2 = 25.475 / 2.0
ANG1 = ANG2 + PIX_ANG * float( BBLEN*2.0 )
ANG0 = 0.0 - ANG2
PIX_DUR = 0.0000321991652
PKT_DUR = PIX_DUR * float( FPPPKT )

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
    print("ANG0=%f ANG1=%f ANG2=%f PIX_ANG=%f" % (ANG0, ANG1, ANG2, PIX_ANG ))
    print(datetime.now())
    self.l0b_fname = l0b_fname + ".h5"
    l0b_fd = h5py.File(self.l0b_fname, "w")

    # Write Standarad Metadata
    # Metadata doesn't work yet with this filenaming convention, so skip this
    # for now. Will need to come back to this.
    if(False):
      fname = 'ECOSTRESS_'+os.path.basename(l0b_fname)
      m = WriteStandardMetadata(l0b_fd, product_specfic_group ="L0BMetadata",
                                pge_name="L0B", local_granule_id=fname,
                                build_id="0.0", pge_version="0.0", orbit_based=True )
      fname = os.path.basename(l0b_fname)
      m.set("LocalGranuleID", fname)
      a = self.l0b_fname.split('_')
      b = a[2].split('T')
      m.set("RangeBeginningDate", b[0])
      m.set("RangeBeginningTime", b[1])
      b = a[3].split('T')
      m.set("RangeEndingDate", b[0])
      m.set("RangeEndingTime", b[1])
      m.write()

    # Write ancillary dataset
    # Build part of ANC records from limited RTD data in ENG file
    print("Reading ENG file %s" % self.l1a_eng_fname)
    l1e = h5py.File(self.l1a_eng_fname,"r")
    anc_buf =''
    for t in (295, 325):
      rtd = l1e["/rtdBlackbodyGradients/RTD_%dK" % t]
      l, = rtd.shape
      anc_buf += " RTD"'%d' % t + "K:"
      for i in range(l):
        anc_buf +=  '%16.10e' % rtd[i]

    # copy data from raw attitude/ephemeris file
    att_fd = h5py.File(self.l1a_raw_att_fname, "r") 
    aq=att_fd["Attitude/quaternion"]
    aqc, aqr = aq.shape
    at=att_fd["Attitude/time_j2000"]
    ep=att_fd["Ephemeris/eci_position"]
    epc, epr = ep.shape
    ev=att_fd["Ephemeris/eci_velocity"]
    et=att_fd["Ephemeris/time_j2000"]

    # create ancillary data set with variable strings
    print("Creating HK Group")
    hk_g = l0b_fd.create_group("/hk")
    st = h5py.special_dtype(vlen=str)
    anc_dat = hk_g.create_dataset("packet", shape=(aqc,1), dtype=st)
    # create housekeeping dataset template with fixed strings
    # hk_dat = hk_g.create_dataset("packet", shape=(aqc,1), maxshape=(None,), dtype='S2048', chunks=(PKTPS,) )

    # Copy into HK data set
    for i in range( aqc ):
      anc_dat[i]='Quat'+ ' %16.10e' % at[i]
      # var = 'Quat' + ' %16.10e' % at[i]
      # anc_dat[i] = anc_dat[i] + var.ENCODe("ascii","ignore")
      for j in range(aqr):
        anc_dat[i] = anc_dat[i] + ' %16.10e' % aq[i,j]
      anc_dat[i] = anc_dat[i] + ' Eph' + ' %16.10e' % et[i]
      for j in range(epr):
        anc_dat[i] = anc_dat[i] + ' %16.10e' % ep[i,j]
      for j in range(epr):
        anc_dat[i] = anc_dat[i] + ' %16.10e' % ev[i,j]
      anc_dat[i] = anc_dat[i] + anc_buf

    # create FLEX packet
    flex_g = l0b_fd.create_group("/flex")
    # create packet dataset template
    flex_d = flex_g.create_dataset("packet", shape=(1,PKT_LEN), maxshape=(None, PKT_LEN), dtype='uint16', chunks=(PKTPS,PKT_LEN) )

    # initialize packet header
    hdr = np.zeros( (HDR_LEN,1), dtype=np.uint16 )
    # packet header SYNC
    hdr[HSYNC], hdr[HSYNC+1] = 0xcccc, 0x5555
    hdr[PLEN], hdr[PLEN+1] = PKT_LEN*2 & 0xffff, (PKT_LEN>>15) & 0xffff

    # running count of packets
    tot_pkt = 0
    # running count of image lines
    tot_lines = 0
    # *** packet ID adjust for out of order scenes ***
    pkt_id = 0

    # working array including PIX and BB, and 1 packet
    bufsiz = FPB3 + FPPPKT
    pix_buf = np.zeros( ( PPFP, bufsiz, BANDS ), dtype=np.uint16 )
    pix_ptr = 0
    pix_dat = [b for b in range(BANDS)]
    b295 = [b for b in range(BANDS)]
    b325 = [b for b in range(BANDS)]
    angnadir = 180.0

    # process scenes make sure to do it in order
    total_scenes = len(self.scene_files)
    for v in range( total_scenes ):
      scene = self.scene_files[v][0]
      l1a_raw_pix_fname = self.scene_files[v][0]
      l1a_bb_fname = self.scene_files[v][1]

      # open raw pixel data file
      pix_fd = h5py.File(l1a_raw_pix_fname, "r")

      # Also get simulated black body data
      bb_fd = h5py.File(l1a_bb_fname, "r")

      # link to pixel and bb datsasets
      for b in range( BANDS ):
        pix_dat[b] = pix_fd["/UncalibratedPixels/pixel_data_%d" %(b+1)]
        b295[b] = bb_fd["/BlackBodyPixels/B%d_blackbody_295K" % (b+1)]
        b325[b] = bb_fd["/BlackBodyPixels/B%d_blackbody_325K" % (b+1)]

      pix_2k=pix_fd["/Time/line_start_time_j2000"]

      # lines and pix per scene (assume all BANDS are the same)
      lines, pix = pix_dat[0].shape
      tot_lines = tot_lines + lines
      l = 0
      # pkts for scene
      tot_pkt = int( ( FPB3*tot_lines/PPFP + FPPPKT -1 ) / FPPPKT )
      # extend packet dataset to new total
      flex_d.resize( tot_pkt, 0 )
      print("\n ===  CREATE_FILE SCENE=%d TOTAL=%d PIX_PTR=%d tot_lines=%d tot_pkt=%d" % (v, total_scenes, pix_ptr, tot_lines, tot_pkt))

      # Iterate through data lines in current scene 256 lines at a time
      while l < lines:

        # copy pix and BB data to buffer at pkt offset
        ps1 = pix_ptr; pe1 = ps1 + FPPSC
        ps2 = pe1; pe2 = ps2 + BBLEN
        ps3 = pe2; pe3 = ps3 + BBLEN

        # assemble pix and bb data into buffer, with offset from previous buffer
        for b in range( BANDS ):
          pix_buf[:,ps1:pe1,b] = pix_dat[b][l:l+PPFP,:]
          pix_buf[:,ps2:pe2,b] = b295[b][l:l+PPFP,:]
          pix_buf[:,ps3:pe3,b] = b325[b][l:l+PPFP,:]

        # step through buffer in packet steps (FPPPKT) starting from 0
        bts = 0
        bte = pix_ptr + FPB3
        t2k = pix_2k[l]
        angnadir = 180.0 - angnadir
        mangle = ANG0
        print("====  ", datetime.now(), "  ====")
        print("L=%d T2K=%20.16e ANGNADIR=%3.1f BTE=%d PIX_PTR=%d PS1=%d PS2=%d PS3=%d PE3=%d" %(l,t2k,angnadir,bte,pix_ptr,ps1,ps2,ps3,pe3))
        while bts < bte:

          # see where current buffer pointer is
          pe1 = bts + FPPPKT
          # print("SCENE=%s PKT_ID=%d MANGLE=%f BTS=%d BTE=%d" %(scene, pkt_id, mangle, bts, bte))
          # write a packet
          if pe1 <= bte:

            # write next packet header
            hdr[PCNT], hdr[PCNT+1] = pkt_id&0xffff, (pkt_id>>16)&0xffff
            # *** generate ENCODer values from -12.738 to +12.738+BB ***
            for i in range( ENCOD, ENCOD + FPPPKT*2, 2 ):
              angle = mangle + angnadir
              if angle >= 0.0: j = int( ( angle ) / ANG_INC )
              else: j = int( ( angle+360.0 ) / ANG_INC )
              #print("PKT=%d I=%d angle=%f, ENCOD=%d" % (i, pkt_id, mangle, j) )
              hdr[i], hdr[i+1] = j & 0xffff, (j>>16) & 0xffff
              mangle = mangle + PIX_ANG
              if mangle >= ANG1: mangle = ANG0
            #  *** set time codes to count of J2K microsecods for now *** 
            pkt_2k = int( t2k*1000000.0 )
            for i in range( FTIME, FTIME+4 ):
              hdr[i] = pkt_2k & 0xffff
              pkt_2k = pkt_2k>>16
            # generate header checksum
            hdr[HSUM],hdr[HSUM+1] = 0,0
            for i in range( 0, HSUM, 2 ):
              hdr[HSUM],hdr[HSUM+1] = hdr[HSUM]^hdr[i],hdr[HSUM+1]^hdr[i+1]
            # copy to file
            flex_d[pkt_id, 0:HDR_LEN] =  hdr[:,0]

            # write packet data
            # packet position
            ptr = HDR_LEN
            # initialize data checksum using hdr buffer
            hdr[HSUM],hdr[HSUM+1] = 0,0
            for b in range( BANDS ):
              # step through FPs per packet
              for i in range( bts, pe1 ):
                #write pix data
                flex_d[pkt_id, ptr:ptr+PPFP] = pix_buf[:,i,b]
                ptr = ptr + PPFP
              # generate data checksum
              for i in range( bts, pe1, 2 ):
                for j in range( PPFP ):
                  hdr[HSUM] = hdr[HSUM]^pix_buf[j,i,b]
                  hdr[HSUM+1] = hdr[HSUM+1]^pix_buf[j,i+1,b]
            # write data checksum
            flex_d[pkt_id,DSUM:DSUM+2] = hdr[HSUM:HSUM+2,0]
            # next point in pix_buf
            bts = pe1
            # next packet
            pkt_id += 1
            t2k += PKT_DUR

            # reached end of valid data in current pix_buf
            if bts == bte:
              # reset offset into next pix_buf
              pix_ptr = 0
              print("End PIX_BUF SCENE=%d BTS=%d PKT_ID=%d ANG=%14.8e" %(v,bts,pkt_id,mangle))

          else:
            # at the remainder of current pix_buf
            print("Remainder SCENE=%d BTE=%d BTS=%d PKT_ID=%d ANG=%14.8e" % (v,bte, bts,pkt_id,mangle))

            # set offset to next pix_buf
            pix_ptr = bte - bts
            # move remainder data to front of pix_buf
            for b in range( BANDS ):
              pix_buf[:,:pix_ptr,b] = pix_buf[:,bts:bte,b]
            # escape bts while loop to go to next scene
            if v+1 < total_scenes or l+PPFP < lines: bts = bte
            # last runt packet of last scene< fill remaining with dummy
            else:
              bts = 0
              bte = FPPPKT
              print("Final runt packet: %d" % pix_ptr )
              for b in range( BANDS ):
                for i in range( pix_ptr, FPPPKT ):
                  for j in range( PPFP ):
                    pix_buf[ j, i, b ] = 0
          # end writing current packet

        # next line in scene
        l += PPFP
        # end copying current pix_buf to packets

      # end writing packets for current scene file
    # *** take care of runt packet of last scene ***
    print("End all scenes, TOT_LINES=%d runt PIX_PTR=%d" % (tot_lines, pix_ptr) )
    # end scene files loop

    # Write L0B metadata
    print("Writing L0BMetadata to L0B file %s" % self.l0b_fname )
    l0b_mg = l0b_fd["L0BMetadata"]
    l0b_pl = l0b_mg.create_dataset("PacketList", shape=(tot_pkt,1), dtype="uint32")
    l0b_ps = l0b_mg.create_dataset("PacketStatus", shape=(tot_pkt,1), dtype="uint32")
    for i in range( tot_pkt ):
      l0b_pl[i] = i
      l0b_ps[i] = 0
    l0b_ps.attrs["PacketPercentage"] = "1.00000000"
    l0b_ifl = l0b_mg.create_dataset("InputFileList", shape=(len(2*self.scene_files),1), dtype=st)
    for v in range(len( self.scene_files )):
      l0b_ifl[v*2] = self.scene_files[v][1]
      l0b_ifl[v*2+1] = self.scene_files[v][2]

    print(datetime.now())
