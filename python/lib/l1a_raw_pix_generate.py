from geocal import *
import h5py
import shutil
import re
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
CNT_DUR = (60/25.4)/float( MAX_FPIE )  # = 1.3504 microsecond
ANG_INC = 360.0 / float( MAX_FPIE )  # = 0.000205803 deg
PIX_ANG = 25.475 / float( FPPSC )  # = 0.004717592 deg
PIX_EV = PIX_ANG / ANG_INC  # = 22.92289 counts/pix
PIX_DUR = 0.0000321982
# Black body pixels are BEFORE image pixels
ANG1 = 25.475 / 2.0
ANG0 = 360.0 - ANG1 - PIX_ANG * float( BBLEN*2.0 )

class L1aRawPixGenerate(object):
  '''This generates a L1A_RAW_PIX, L1A_BB, L1A_ENG and L1A_RAW_ATT
  files from a L0B input.'''
  def __init__(self, l0b, scene_file, run_config = None):
    '''Create a L1aRawPixGenerate to process the given L0 file. 
    To actually generate, execute the 'run' command.'''
    self.l0b = l0b
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

  def get_flex_time( self, flex_buf ):

    fswt = flex_buf[0,FTIME+3]
    fpie_clk = flex_buf[0,DTIME+3]
    fsw_clk = flex_buf[0,DSYNC+3]
    for i in range(1,4):
      fswt = fswt << 16 | flex_buf[ 0, FTIME+3-i ]
      fpie_clk = fpie_clk << 16 | flex_buf[ 0, DTIME+3-i ]
      fsw_clk = fsw_clk << 16 | flex_buf[ 0, DSYNC+3-i ]
    gs = (fswt>>32) & 0xffffffff
    ns = fswt & 0xffffffff
    gt = float(gs) + ( float(ns)/1000.0 + fpie_clk - fsw_clk )/1000000.0
#    print("GFT: FSWT=%x FC=%d PC=%d GS=%d NS=%d gt=%f" % (fswt, fpie_clk, fsw_clk, gs, ns, gt ) )
    return gt

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

    ' open scene start/stop times file '
    sf = open( self.scene_file, "r" )

    self.fin = h5py.File(self.l0b,"r", driver='core')
    flex_pkt = self.fin["/flex/packet"]
    tot_pkts, pkt_siz = flex_pkt.shape
    print("Opened L0B file %s, TOT_PKTS=%d, PKT_SIZ=%d" % (self.l0b, tot_pkts, pkt_siz ) )
    if pkt_siz != PKT_LEN:
      print("**** Packet size from L0 file:%s (%d) dffers from spec (%d)" % (self.l0b, pkt_siz, PKT_LEN ))
    else:
      print("Packet size=%d, SPEC=%d, match in file %s" %( pkt_siz, PKT_LEN, self.l0b ) )

    pkt_stat = self.fin["/L0BMetadata/PacketStatus"]
    if pkt_stat.shape[0] != tot_pkts:
      print("**** Number of packet stats not equal to number of packets %d ****" % pkt_stat.shape[0] )

    ' initialize some output pointers for different bands '
    pix_dat = [b for b in range(BANDS)]
    b295 = [b for b in range(BANDS)]
    b325 = [b for b in range(BANDS)]

    pkt_idx = 0

    pix_buf = np.zeros( ( PPFP, FPPSC, BANDS ), dtype=np.uint16 )
    flex_buf = np.zeros( (2,pkt_siz), dtype=np.uint16 )

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
      pktp0t = Time.time_gps(0.0)  # Initialize to GPS 9
      while pktp0t < ss and pkt_idx<tot_pkts:
        if pkt_stat[ pkt_idx ] == 0:  # skip invalid packets
          good_pkt += 1
          flex_buf[0:] = flex_pkt[ pkt_idx,:]

          gt = self.get_flex_time( flex_buf )

          pktp0t = Time.time_gps(gt)
          print("Packet %d, time=%f, SS=%f" % ( pkt_idx, pktp0t.j2000, ss.j2000 ) )
        ' end skip invalid backet '
        pkt_idx += 1
        pkt_cnt += 1
      ' end searching for packet matching scene start time '
      if pkt_idx >= tot_pkts:
        print("Could not find Scene %s time %s (%fJ2K) in file %s PKT=%d" % ( scene_id, sc_start_time, ss.j2000, self.l0b, pkt_idx ) )
        return -1

      ' found scene start time in previous packet '
      if pktp0t >= ss:
        print("Decrement counts PKT_IDX=%d PKT_CNT=%d" %(pkt_idx, pkt_cnt))
        pkt_idx -= 1
        pkt_cnt -= 1
        good_pkt -= 1
      print("Found scene %s start time %fJ2K in packet %d FP0 time=%s" % ( scene_id, ss.j2000, pkt_idx, str(pktp0t) ) )

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
      pix_time = l1a_ptg.create_dataset("line_start_time_j2000", shape=(SCPS,), dtype="f8" )
      ' FPIE encoder value of each focal plane in scan '
      pix_ev = l1a_peg.create_dataset("EncoderValue", shape=(SCPS,FPPSC), dtype="u4" )
      ' Image and BB pixel dataset for each band '
      for b in range( BANDS ):
        pix_dat[b] = l1a_upg.create_dataset("pixel_data_%d" %(b+1), shape=(LPS,FPPSC), dtype="u2" )
        b295[b] = l1a_bpg.create_dataset("B%d_blackbody_295K" %(b+1), shape=(LPS, BBLEN), dtype="u2" )
        b325[b] = l1a_bpg.create_dataset("B%d_blackbody_325K" %(b+1), shape=(LPS, BBLEN), dtype="u2" )

      # First focal plane of scene in current packet
      p0 = int( (pktp0t.j2000-ss.j2000)/ PIX_DUR + 0.5 )
      ' loop through scans '
      #  assume BB data start 2 packets before image data for now
      pkt_idx -= 2
      for scan in range( SCPS ):

        line = scan*PPFP
        '==== copy BB pixels for scan ===='
        dp = 0  # initialize output pointer
        '*** The following BB code assumed BBLEN = FPPPKT '
#  Current data order is FP[0]*BANDS, FP[1]*BANDS...FPPPKT*BANDS, each FP is PPFP pixels
        p1 = HDR_LEN + p0 * PPFP * BANDS
        if p0 > 0:
          fpc = FPPPKT - p0  #  focal plane count in current packet
          ' copy partial FPs from packet '
          print("Copy partial FPC=%d PKT=%d P0=%d" % (fpc, pkt_idx, p0) )
# find starting EV for BB1
          flex_buf[:,:] = flex_pkt[pkt_idx:pkt_idx+2,:]
          if pkt_stat[pkt_idx] == 0:
            good_bb += 1
          else:
            flex_buf[0,HDR_LEN:] = 0xffff
          if pkt_stat[pkt_idx+1] == 0:
            good_bb += 1
          else:
            flex_buf[1,HDR_LEN:] = 0xffff
          for i in range( fpc ):
            ps = i*PPFP*BANDS + p1
            for b in range( BANDS ):
              ptr = b*PPFP + ps
              b295[b][line:line+PPFP,dp+i] = flex_buf[0,ptr:ptr+PPFP]
              b325[b][line:line+PPFP,dp+i] = flex_buf[1,ptr:ptr+PPFP]
          dp = fpc
          pkt_idx += 1
          fpc = p0  # remainder BB FPs in next packets
          p1 = HDR_LEN
        else:
          fpc = FPPPKT

        print("Second BB set copy P0=%d FPC=%d idx=%d" % ( p0, fpc, pkt_idx ) )
# find starting EV for BB2
        flex_buf[:,:] = flex_pkt[pkt_idx:pkt_idx+2,:]
        if pkt_stat[pkt_idx] == 0:
          if p0==0: good_bb += 1
        else:
          flex_buf[0,HDR_LEN:] = 0xffff
        if pkt_stat[pkt_idx+1] == 0:
          if p0==0: good_bb += 1
        else:
          flex_buf[1,HDR_LEN:] = 0xffff
        for i in range( fpc ):
          ps = i*PPFP*BANDS + p1
          for b in range( BANDS ):
            ptr = b*PPFP + ps
            b295[b][line:line+PPFP,dp+i] = flex_buf[0,ptr:ptr+PPFP]
            b325[b][line:line+PPFP,dp+i] = flex_buf[1,ptr:ptr+PPFP]
        if p0 == 0:
          pkt_idx += 2  # reset to first image packet
        else:
          pkt_idx += 1
        bb_cnt += 2   # increment BB packet count
        ' end copy BB pixels for current scan '

        ' extract first FP time from packet '
        flex_buf[0,:] = flex_pkt[pkt_idx,:]
        if pkt_stat[ pkt_idx ] == 0:

          gt = self.get_flex_time( flex_buf ) + p0*PIX_DUR

        else:
          print("*** Bad packet %d, can not calculate FP time ***" % pkt_idx )
          return -1
        ' record starting pixel time in j2k for current scan '
        ' *** FSW time, FPIE clock, and PIX clock may be BIGENDIAN *** '
        pix_time[scan] = Time.time_gps( gt ).j2000
        scfp_cnt = 0  #  count of total copied FPs for current scan
        dp = 0  #  output pointer
        fpc = FPPPKT - p0
        print("SCENE=%s SCAN=%d GT=%f p2k=%f PKT=%d P0=%d" %(scene_id, scan, gt, pix_time[scan], pkt_idx, p0))

        '==== copy image pixels for current scan ===='
        while scfp_cnt < FPPSC:
          p1 = HDR_LEN + p0 * PPFP * BANDS  #  word offset first FP in packet
          if scfp_cnt + fpc > FPPSC:  # at end of current scan
            fpc = FPPSC - scfp_cnt    # remaining FPs in packet
            p0 = fpc                # save first FP in packet for next scan
            idx_inc = 0            # stay on same packet
          else:
            idx_inc = 1
# find starting EV for IMG
          flex_buf[0,:] = flex_pkt[pkt_idx,:]
          for j in range( fpc ):
            ps = j*PPFP*BANDS + p1
            for b in range( BANDS ):
              ptr = b*PPFP + ps
              pix_buf[:,dp+j, b] = flex_buf[0,ptr:ptr+PPFP]
            ' also record FPIE encoder value for each FP '
            pix_ev[scan, dp+j] = flex_buf[0,ENCOD+j*2] | flex_buf[0,ENCOD+j*2+1]<<16
          scfp_cnt += fpc  #  increment total FPs copied
          dp += fpc        #  increment pointer to output file
          if idx_inc == 1:
            if pkt_stat[ pkt_idx] == 0:
              good_pkt += idx_inc
            else:
              flex_buf[0,HDR_LEN:] = 0xffff
            pkt_idx += idx_inc
            pkt_cnt += idx_inc
            p0 = 0
            fpc = FPPPKT
### just for printout of packet header
          pktid = flex_buf[0,PKTID] | ( flex_buf[0,PKTID+1] << 16 )

          gt = self.get_flex_time( flex_buf )

          t2k = Time.time_gps(gt).j2000
          utc = str(Time.time_gps(gt))[:26]
          fpie = flex_buf[0,ENCOD] | ( flex_buf[0,ENCOD+1] << 16 )
          angle = float( fpie ) * ANG_INC
          print("PKT=%d ID=%d GPS=%f T2K=%f UTC=%s FPIE0=%d ANGLE=%f" % (pkt_idx-1,pktid,gt,t2k,utc,fpie,angle))
###
        for b in range( BANDS):  # write scan to output file
          pix_dat[b][line:line+PPFP,:] = pix_buf[:,:,b]

        ' end copy image pixels for current scan '
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
    hk_pkt = self.fin["/hk/packet"]
    aqc = hk_pkt.shape[0]

    ' create engineering file and datasets '
    print("crerating ENG and ATT files, AQC=%d" % aqc )
    feng = self.create_file( "L1A_ENG", onum, None, o_start_time, o_end_time, primary_file=True )
    eng = h5py.File( feng, "r+", driver='core' )
    eng_g = eng.create_group("/rtdBlackbodyGradients")
    rtd295 = eng_g.create_dataset("RTD_295K", shape=(5,), dtype='f4')
    rtd325 = eng_g.create_dataset("RTD_325K", shape=(5,), dtype='f4')

    ' create raw attitude/ephemeris file and datasets '
    fatt = self.create_file("L1A_RAW_ATT", onum, None, o_start_time, o_end_time, prod=False)
    att = h5py.File( fatt, "r+", driver='core' )
    att_g = att.create_group("/Attitude")
    a2k = att_g.create_dataset("time_j2000", shape=(aqc,), dtype='f8' )
#pix_time = l1a_ptg.create_dataset("line_start_time_j2000", shape=(SCPS,), dtype="f8" )
    q = att_g.create_dataset("quaternion", shape=(aqc,4), dtype='f8' )
    eph_g = att.create_group("/Ephemeris")
    e2k = eph_g.create_dataset("time_j2000", shape=(aqc,), dtype='f8' )
    pos = eph_g.create_dataset("eci_position", shape=(aqc,3), dtype='f8' )
    vel = eph_g.create_dataset("eci_velocity", shape=(aqc,3), dtype='f8' )

    for i in range(aqc):
      hk = hk_pkt[i].split(' ')
      a2k[i] = float( hk[1] )
      for j in range(4):
        q[i,j] = float( hk[j+2] )
      e2k[i] = float( hk[7] )
      for j in range(3):
        pos[i,j] = float( hk[j+8] )
        vel[i,j] = float( hk[j+11] )
    att.close()
    for j in range(5):
      rtd295[j] = float( hk[j+15] )
      rtd325[j] = float( hk[j+21] )
    eng.close()

    # Write out a dummy log file
    print("This is a dummy log file", file = self.log)
    self.log.flush()
    print("====  End run ", datetime.now(), "  ====")
