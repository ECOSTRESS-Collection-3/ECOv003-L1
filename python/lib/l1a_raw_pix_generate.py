## from geocal import *
import h5py
import shutil
import re
import os
import numpy as np
from .write_standard_metadata import WriteStandardMetadata
from .misc import ecostress_file_name
from geocal import Time
from datetime import datetime

'''
ydt = "2016-12-16T10:02:12.34567890"

import time
t_struct=time.strptime(ydt,TPAT)
time.strptime(ydt,TPAT)
time.struct_time(tm_year=2016, tm_mon=12, tm_mday=16, tm_hour=10, tm_min=2, tm_sec=12, tm_wday=4, tm_yday=351, tm_isdst=-1) 

datetime.strptime(ydt,TPAT)
->datetime.datetime(2016, 12, 16, 10, 2, 12, 345000)
a.microsecond
->345000

By packets:

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

TPAT="%Y-%m-%dT%H:%M:%S.%f"
FPAT="%Y%m%dT%H%M%S"
J2KS=946728000  # calendar.timegm(time.strptime("2000-01-01T12:00:00.000",TPAT))
GPSS=315964800  # calendar.timegm(time.strptime("1980-01-06T00:00:00.000",TPAT))
GP2K = J2KS - GPSS  # difference
# UTCS = datetime.utcfromtimestamp(int(T2K+J2KS)) UTC seconds from J2K time
# UTCS = datetime.utcfromtimestamp(int(GPS+GPSS)) UTC seconds from GPS time

' short word offsets into FPIE packet array '

' packet primary header '
HSYNC = 0
PKTID = HSYNC + 2
ENCOD = PKTID + 2
ISTATE = ENCOD + 128
FTIME = ISTATE + 2
DTIME = FTIME + 4
DSYNC = DTIME + 4
HDR_LEN = 284
PKT_LEN = 98590

BANDS = 6
' number of pixels per focal plane '
PPFP = 256
' number of focal planes per full scan '
FPPSC = 5400
' number of FPs in each BB per scan '
BBLEN = 64
' Total FPs per scan including hot and cold BB '
FPB3 = FPPSC + BBLEN*2
' number of FPs per raw packet '
FPPPKT = 64
' Scans per scene '
SCPS = 44
' lines per scene '
LPS = PPFP * SCPS
' standard packets per scene rounded up '
PPSC = int( (SCPS*FPB3+FPPPKT-1) / FPPPKT )

MAX_FPIE=1749248
CNT_DUR = (60.0/25.4)/float( MAX_FPIE )  # = 1.3504 microsecond
ANG_INC = 360.0 / float( MAX_FPIE )  # = 0.000205803 deg
PIX_ANG = 25.475 / float( FPPSC )  # = 0.004717592 deg
PIX_EV = PIX_ANG / ANG_INC  # = 22.92289 counts/pix
FP_DUR = 0.0000321982
# Black body pixels are BEFORE image pixels
ANG1 = 25.475 / 2.0
ANG0 = 360.0 - ANG1 - PIX_ANG * float( BBLEN*2.0 )

class L1aRawPixGenerate(object):
  '''This generates a L1A_RAW_PIX, L1A_BB, L1A_ENG and L1A_RAW_ATT
  files from a L0B input.'''
  def __init__(self, l0b, osp_dir, scene_file, run_config = None):
    '''Create a L1aRawPixGenerate to process the given L0 file. 
    To actually generate, execute the 'run' command.'''
    self.l0b = l0b
    self.osp_dir = osp_dir
    self.scene_file = scene_file
    self.run_config = run_config

  def create_file(self, prod_type, orbit, scene, start_time, end_time, primary_file = False, prod=True):
    '''Create the file, generate the standard metadata, and return
    the file name.'''
    '''
    if(scene is None):
      basegroup = "/Data"
    else:
      basegroup = "/Data/Scene_%d" % scene
    bdate = self.fin[basegroup + "/StandardMetadata/RangeBeginningDate"].value
    btime = self.fin[basegroup + "/StandardMetadata/RangeBeginningTime"].value
    bdtime = Time.parse_time("%sT%sZ" % (bdate, btime))
    edate = self.fin[basegroup + "/StandardMetadata/RangeEndingDate"].value
    etime = self.fin[basegroup + "/StandardMetadata/RangeEndingTime"].value
    '''
    bdtime = start_time[0:4] + start_time[5:7] + start_time[8:13] + start_time[14:16] + start_time[17:19]
    #fname = ecostress_file_name(prod_type, orbit, scene, start_time)
    if ( prod ):
      pre = "ECOSTRESS_" + prod_type + "_"
    else:
      pre = prod_type + "_"
    if ( scene is None ):
      fname = pre + orbit + "_" + bdtime + "_0100_05.h5"
    else:
      fname = pre + orbit + "_" + scene + "_" + bdtime + "_0100_05.h5"
    if(primary_file):
      self.log_fname =  os.path.splitext(fname)[0] + ".log"
      self.log = open(self.log_fname, "w")
    fout = h5py.File(fname, "w", driver='core')
    m = WriteStandardMetadata(fout,
        product_specfic_group = prod_type + "Metadata",
        proc_lev_desc = 'Level 1A Raw Parameters',
        pge_name="L1A_RAW_PIX", local_granule_id=fname,
        build_id = '0.20', pge_version='0.20',
        orbit_based = (scene is None))
    if(self.run_config is not None):
      m.process_run_config_metadata(self.run_config)
    m.set("RangeBeginningDate", start_time[0:10])
    m.set("RangeBeginningTime", start_time[11:26])
    m.set("RangeEndingDate", end_time[0:10])
    m.set("RangeEndingTime", end_time[11:26])
    m.write()
    fout.close()
    return fname

  def run(self):

    ''' Do the actual generation of data.'''
    print("====  Start run ", datetime.now(), "  ====")
    self.log = None

    m=re.search('L0B_(.+?)_',self.l0b)
    if m:
      onum = m.group(1)
    else:
      print("Could not find orbit number from L0B file name %s" %self.l0b)
      return -1

#  Get EV start codes for BB and IMG pixels
    ev_codes = np.zeros( (3,2), dtype=np.int32 )
    ' open EV codes file '
    ef = open( self.osp_dir + "ev_codes.txt", "r")
    i = 0
    for evl in iter( ef ):
      e0, e1, e2 = evl.split("	")
      ev_codes[i,0] = int(e1)
      ev_codes[i,1] = int(e2)
      print("EV_CODES[%d](%s) = %d, %d" % (i,e0,ev_codes[i,0],ev_codes[i,1] ))
      i += 1
    ef.close()

# open scene start/stop times file
    sf = open( self.scene_file, "r" )

# open L0B file
    self.fin = h5py.File(self.l0b,"r", driver='core')
    bip=self.fin["flex/bip"]
    lid=self.fin["flex/id_line"]
    pid=self.fin["flex/id_packet"]
    flex_st=self.fin["flex/state"]
    fswt=self.fin["flex/time_fsw"]
    fpie_sync=self.fin["flex/time_sync_fpie"]
    fsw_sync=self.fin["flex/time_sync_fsw"]
    att=self.fin["hk/bad/hr/attitude"]
    pos=self.fin["hk/bad/hr/position"]
    vel=self.fin["hk/bad/hr/velocity"]
    att_fsw=self.fin["hk/bad/hr/time_fsw"]
    att_time=self.fin["hk/bad/hr/time"]
    dp_mode=self.fin["hk/status/mode/dpuio"]
    op_mode=self.fin["hk/status/mode/op"]
    bb1_ms=self.fin["hk/status/motor/bb1"]
    bb2_ms=self.fin["hk/status/motor/bb2"]
    mode_ms=self.fin["hk/status/motor/mode"]
    pstate_ms=self.fin["hk/status/motor/pstate"]
    bbt=self.fin["hk/status/temperature"]
    bb_time=self.fin["hk/status/time"]
    bb_fsw=self.fin["hk/status/time_fsw"]

    tot_pkts = bip.shape[0]
    print("Opened L0B file %s, TOT_PKTS=%d" % (self.l0b, tot_pkts ) )

    ' initialize some output pointers for different bands '
    pix_dat = [b for b in range(BANDS)]
    b295 = [b for b in range(BANDS)]
    b325 = [b for b in range(BANDS)]

    pkt_idx = 0

    pix_buf = np.zeros( ( PPFP, FPB3+FPPPKT, BANDS ), dtype=np.uint16 )
    ev_buf = np.zeros( FPB3+FPPPKT, dtype=np.uint32 )
    flex_buf = np.zeros( (FPPPKT, PPFP, BANDS), dtype=np.uint16 )

    o_start_time = None
    for sfl in iter( sf ):  # iterate through scenes from scene start/stop file
      orbit, scene_id, sc_start_time, sc_end_time = sfl.split( "	" )
      if o_start_time == None: o_start_time = sc_start_time
      o_end_time = sc_end_time
      ' Get scene start and end times (UTC) from scene file entry '
      dt = sc_start_time[0:26].replace( 'T', ' ' ) + ' UTC'
      ss = Time.parse_time( dt )
      dt = sc_start_time[0:26].replace( 'T', ' ' ) + ' UTC'
      se = Time.parse_time( dt )
      print("====  ", datetime.now(), "  ====")
      print("SCENE=%s START=%s END=%s SS=%f SE=%f" % ( scene_id, sc_start_time, sc_end_time, ss.j2000, se.j2000 ) )

      good_pkt = 0
      good_bb = 0
      pkt_cnt = 0
      bb_cnt = 0

      ' search for packet containing scene start time '
      ' *** Account for actual time of camera switch-on from mirror angle *** '
      ' *** Account for missing packets, assume in time sequence *** '
      pktp0t = Time.time_gps(0.0)  # Initialize to GPS 0
      while pktp0t < ss and pkt_idx<tot_pkts:
        good_pkt += 1
        gt = fswt[pkt_idx] + float(fpie_sync[pkt_idx] - fsw_sync[pkt_idx]) /1000000.0

        pktp0t = Time.time_gps(gt)
        print("Packet %d ID=%d time=%f, SS=%f" % ( pkt_idx, pid[pkt_idx], pktp0t.j2000, ss.j2000 ) )
        pkt_idx += 1
        #pkt_cnt += 1
      ' end searching for packet matching scene start time '
      if pkt_idx >= tot_pkts:
        print("Could not find Scene %s time %s (%fJ2K) in file %s PKT=%d" % ( scene_id, sc_start_time, ss.j2000, self.l0b, pkt_idx ) )
        return -1

      ' found scene start time in previous packet '
      if pktp0t >= ss:
        print("Decrement counts PKT_IDX=%d PKT_CNT=%d" %(pkt_idx, pkt_cnt))
        pkt_idx -= 1
        #pkt_cnt -= 1
        #good_pkt -= 1
      pkt_idx -= 2  #  2 black bodies are ahead of image packets
      if pkt_idx == 0: pktid0 = 0
      else: pktid0 = pid[pkt_idx-1]
      print("Found scene %s start time %fJ2K in packet[%d]=%d (id0=%d) FP0 time=%s" % ( scene_id, ss.j2000, pkt_idx, pid[pkt_idx], pktid0, str(pktp0t) ) )

      ' create scene file and image pixel, J2K, and FPIE ENC groups '
      pname = self.create_file( "L1A_RAW_PIX", onum, scene_id, sc_start_time, sc_end_time, prod=False )
      l1a_fp = h5py.File( pname, "r+", driver='core' )
      l1a_upg = l1a_fp.create_group("/UncalibratedPixels")
      l1a_ptg = l1a_fp.create_group("/Time")
      l1a_peg = l1a_fp.create_group("/FPIEencoder")

      ' create BB file and BlackBodyPixels group '
      bname = self.create_file( "L1A_BB", onum, scene_id, sc_start_time, sc_end_time, prod=True )
      l1a_bp = h5py.File( bname, "r+", driver='core' )
      l1a_bpg = l1a_bp.create_group("/BlackBodyPixels")

      ' create datasets '
      ' Starting time of first focal plane in each scan '
      pix_time = l1a_ptg.create_dataset("line_start_time_j2000", shape=(1,), maxshape=(None,), dtype="f8" )
      pix_time.attrs['Description']='J2000 time of first pixel in line'
      pix_time.attrs['Units']='second'
      ' FPIE encoder value of each focal plane in scan '
      pix_ev = l1a_peg.create_dataset("EncoderValue", shape=(1,FPPSC), maxshape=(None,FPPSC), dtype="u4" )
      ' Image and BB pixel dataset for each band '
      for b in range( BANDS ):
        pix_dat[b] = l1a_upg.create_dataset("pixel_data_%d" %(b+1), shape=(1,FPPSC), maxshape=(None,FPPSC), chunks=(PPFP,FPPSC), dtype="u2" )
        pix_dat[b].attrs['Units']='dimensionless'
        b295[b] = l1a_bpg.create_dataset("B%d_blackbody_295K" %(b+1), shape=(1, BBLEN), maxshape=(None,BBLEN), chunks=(PPFP,BBLEN), dtype="u2" )
        b295[b].attrs['Units']='dimensionless'
        b325[b] = l1a_bpg.create_dataset("B%d_blackbody_325K" %(b+1), shape=(1, BBLEN), maxshape=(None,BBLEN), chunks=(PPFP,BBLEN), dtype="u2" )
        b325[b].attrs['Units']='dimensionless'

      # First focal plane of scene in current packet
      dt = pktp0t - ss
      p0 = int( dt/FP_DUR + 0.5 )
      p1 = p0
      ' loop through scans '
      ###  assume BB data start 2 packets before image data for now
      ### pkt_idx -= 2
      line = 0  # line pointer in output image
      dp = 0  # initialize output FP pointer
      scfp_cnt = 0  #  count of total copied FPs for current scan
      pix_buf[:,:,:] = 0xffff  # pre-fill with null values
      ev_buf[:] = 0xffffffff
      for scan in range( SCPS ):
        pix_time.resize( scan+1, 0 )
        gt = fswt[pkt_idx] + float(fpie_sync[pkt_idx] - fsw_sync[pkt_idx]) /1000000.0 + dt
        pix_time[scan] = Time.time_gps( gt ).j2000
        pix_ev.resize( scan+1, 0 )
        for b in range( BANDS ):
          pix_dat[b].resize( line+PPFP, 0 )
          b295[b].resize( line+PPFP, 0 )
          b325[b].resize( line+PPFP, 0 )

        fpc = FPPPKT - p1  # FPs to copy from first packet in scan
        idx_inc = 1
        skip = 0
        while scfp_cnt < FPB3:  # build up a full scan of IMG and BB pix
          if idx_inc == 1:  #  read next packet
            flex_buf[:,:,:] = bip[pkt_idx,:,:,:]
            pktid = pid[pkt_idx]
            skip = (pktid - pktid0 - 1) * FPPPKT
            op = dp + skip
          # end reading new packet

# find starting EV for BB1, BB2, and IMG pixels
          print("SCENE=%s SCAN=%d LINE=%d GT=%f p2k=%f IDX=%d SCFPCNT=%d P1=%d DP=%d OP=%d SKIP=%d FPC=%d" %(scene_id, scan, line, gt, pix_time[scan], pkt_idx, scfp_cnt, p1, dp, op, skip, fpc))
          if op < FPB3:
            print("transposing IDX=%d P1=%d FPC=%d OP=%d" % (pkt_idx, p1, fpc, op) )
            for b in range( BANDS ):  # copy packet data to pixel buffer
              pix_buf[:,op:op+fpc,b] = np.transpose(flex_buf[p1:p1+fpc,:,b])
            ev_buf[op:op+fpc] = lid[pkt_idx,p1:p1+fpc]  #  and current EVs
            scfp_cnt += (fpc + skip)
            dp += (fpc + skip)  #  next FP pointer in pix_buf
            p1 = 0  #  copy whole packets after the first (if partial)
            fpc = FPPPKT
            idx_inc = 1  #  normal packet increment
            pktid0 = pid[pkt_idx]
            pkt_idx += idx_inc
            pkt_cnt += 1
            good_pkt += 1
          else:  #  need to skip to future line
            idx_inc = 0  # do not read a new packet
            print("flushing scan %d packet=%d OP=%d" % (scan, pkt_idx, op))
            if skip > 0:
              print("PKTID mismatch: Expected %d found %d" % (pktid0+1, pktid))
              if dp < FPB3: scfp_cnt = FPB3  # no runt
              dp = op - FPB3 + skip
              skip = dp
          # end copying or skipping pix_buf
        # end filling current pix_buf and ev_buf

        # copy to output file
        pix_ev[scan,:] = ev_buf[:FPPSC]
        for b in range( BANDS ):
          pix_dat[b][line:line+PPFP,:] = pix_buf[:,BBLEN*2:FPB3,b]
          b295[b][line:line+PPFP,:] = pix_buf[:,0:BBLEN,b]
          b325[b][line:line+PPFP,:] = pix_buf[:,BBLEN:BBLEN*2,b]
        good_bb += 2
        bb_cnt += 2
        if skip > 0:
          op = 0
        else:
          op = dp - FPB3
          scfp_cnt -= FPB3
        if op > 0:  # save runt at end
          print("Copying runt PIX and EV DP=%d OP=%d" % (dp, op) )
          pix_buf[:,0:op,:] = pix_buf[:,FPB3:dp,:]
          ev_buf[0:op] = ev_buf[FPB3:dp]
        pix_buf[:,op:,:] = 0xffff
        ev_buf[op:] = 0xffffffff
        dp = op
        line += PPFP
        ' end copy image and BB pixels and EV for current scan '
      ' end scans loop '
      pkt_cnt -= 1
      good_pkt -= 1

      ' record scene completeness '
      pcomp = float( good_pkt ) / float( pkt_cnt )
      sm = l1a_fp['StandardMetadata']
      del sm['AutomaticQualityFlag']
      sm['AutomaticQualityFlag'] = '%16.10e' % pcomp
      bcomp = float( good_bb ) / float( bb_cnt )
      sm = l1a_bp['StandardMetadata']
      del sm['AutomaticQualityFlag']
      sm['AutomaticQualityFlag'] = '%16.10e' % bcomp
      print("====  ", datetime.now(), "  ====")
      print("SCENE %s completed, (%f) %d good out of %d IMG packets, (%f) %d good out of %d BB packets" % ( scene_id, pcomp, good_pkt, pkt_cnt, bcomp, good_bb, bb_cnt ))

      l1a_fp.close()
      l1a_bp.close()
      good_pkt = 0
      pkt_cnt = 0
      good_bb = 0
      bb_cnt = 0
    ' end scene loop '

    ' Read HK packets to build up ENG and raw ATT/EPH files '
    aqc = att.shape[0]

    ' create engineering file and datasets '
    print("crerating ENG and ATT files, AQC=%d" % aqc )
    feng = self.create_file( "L1A_ENG", onum, None, o_start_time, o_end_time, primary_file=True )
    eng = h5py.File( feng, "r+", driver='core' )
    eng_g = eng.create_group("/rtdBlackbodyGradients")
    rtd295 = eng_g.create_dataset("RTD_295K", shape=(aqc,5), dtype='f4')
    rtd325 = eng_g.create_dataset("RTD_325K", shape=(aqc,5), dtype='f4')
    rtdtime = eng_g.create_dataset("time_j2000", shape=(aqc,2), dtype='f8')
    for i in range(aqc):  # *** get conversion factors for temp DN to Kelvins
      rtd295[i,:] = bbt[i,0,:]  #  copy for now
      rtd325[i,:] = bbt[i,1,:]
      '''
      for j in range( 5 ):
        rtd295[i,j] = convert( bbt[i,0,j] )
        rtd325[i,j] = convert( bbt[i,1,j] )
      '''
      rtd295.attrs['Units']='K and XY'
      rtd325.attrs['Units']='K and XY'
      rtdtime[i,0] = Time.time_gps( bb_time[i] ).j2000
      rtdtime[i,1] = Time.time_gps( bb_fsw[i] ).j2000
    eng.close()

    print("====  ", datetime.now(), "  ====")
    ' create raw attitude/ephemeris file and datasets '
    fatt = self.create_file("L1A_RAW_ATT", onum, None, o_start_time, o_end_time, prod=False)
    attf = h5py.File( fatt, "r+", driver='core' )
    att_g = attf.create_group("/Attitude")
    a2k = att_g.create_dataset("time_j2000", shape=(aqc,), dtype='f8' )
    q = att_g.create_dataset("quaternion", shape=(aqc,4), dtype='f8' )
    eph_g = attf.create_group("/Ephemeris")
    e2k = eph_g.create_dataset("time_j2000", shape=(aqc,), dtype='f8' )
    epos = eph_g.create_dataset("eci_position", shape=(aqc,3), dtype='f8' )
    evel = eph_g.create_dataset("eci_velocity", shape=(aqc,3), dtype='f8' )
    for i in range(aqc):
      a2k[i] = Time.time_gps( att_time[i] ).j2000
      e2k[i] = a2k[i]
      #e2k[i] = Time.time_gps( att_fsw[i] ).j2000
    a2k.attrs['Units']='Seconds'
    e2k.attrs['Units']='Seconds'
    q[:,:] = att[:,:]
    q.attrs['Description']='Attitude quaternion,goes from spacecraft to ECI. The coefficient convention used has the real part in the first column.'
    q.attrs['Units']='dimensionless'
    epos[:,:] = pos[:,:]
    epos.attrs['Description']='ECI position'
    epos.attrs['Units']='m'
    evel[:,:] = vel[:,:]
    evel.attrs['Description']='ECI velocity'
    evel.attrs['Units']='m/s'
    attf.close()

    # Write out a dummy log file
    print("This is a dummy log file", file = self.log)
    self.log.flush()
    print("====  End run ", datetime.now(), "  ====")
