## from geocal import *
import h5py
import shutil
import re
import os
import numpy as np
from .write_standard_metadata import WriteStandardMetadata
from .misc import ecostress_file_name, time_split
from geocal import Time
from datetime import datetime

'''
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

Motor control modes (uint8):

0: IDLE
1: SPINNING
2: BLACKBODY_1
3: BLACKBODY_2
4: SUNSAFE
5: MANUAL

kc1 = PRT_313_T( P7_R(raw.AnalogsTemp_BB_COLD_1) )
kc2 = PRT_314_T( P7_R(raw.AnalogsTemp_BB_COLD_2) )
kc3 = PRT_317_T( P7_R(raw.AnalogsTemp_BB_COLD_3) )
kc4 = PRT_315_T( P7_R(raw.AnalogsTemp_BB_COLD_4) )
kc5 = PRT_318_T( P7_R(raw.AnalogsTemp_BB_COLD_5) )
kh1 = PRT_465_T( P7_R(raw.AnalogsTemp_BB_HOT_1) )
kh2 = PRT_466_T( P7_R(raw.AnalogsTemp_BB_HOT_2) )
kh3 = PRT_467_T( P7_R(raw.AnalogsTemp_BB_HOT_3) )
kh4 = PRT_468_T( P7_R(raw.AnalogsTemp_BB_HOT_4) )
kh5 = PRT_469_T( P7_R(raw.AnalogsTemp_BB_HOT_5) )

'''

J2KS=946728000  # calendar.timegm(time.strptime("2000-01-01T12:00:00.000",TPAT))
GPSS=315964800  # calendar.timegm(time.strptime("1980-01-06T00:00:00.000",TPAT))
GP2K = J2KS - GPSS  # difference

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

# Short term, change this to match EcostressTimeTable pixel duration.
# We will want to change this back, but for now change this to match
# existing test data. See Issue #13 in github.
#FP_DUR = 0.0000321982
#FP_DUR = 0.0000322
FP_DUR = 0.000030955332  # this is consistent with FOV of 25.475
PKT_DUR = FP_DUR * float( FPPPKT )
RPM = 25.4
MPER = 60.0/RPM # mirror period = 2.3622047 sec / rev
SC_DUR = MPER/2.0 # half-mirror rotation = 1.1811024 sec
FP_ANG = FP_DUR*RPM*6.0 # FP angle = .0047175926 deg / FP
FOV = FP_DUR*RPM*6.0*FPPSC # field of view = 25.475000 deg / scan
ANG1 = FOV / 2.0
ANG0 = -ANG1
ANG2 = float( int( (ANG1 + FP_ANG*float(BBLEN*2))*1000.0 ) )/1000.0
# FPIE mirror encoder - 50.95 degree swath width
# covered by 25.475 degree of mirror scan.  Mirror
# is 2-sided, so every other scan is 180 degrees apart
MAX_FPIE=1749248
CNT_DUR = 60.0/RPM/float( MAX_FPIE ) - 1.357079461852133e-10  # = 1.3504 microsecond/count
ANG_INC = 360.0 / float( MAX_FPIE )  # = 0.00020580272 deg/count
FP_EV = FP_DUR*RPM*MAX_FPIE / 60.0 # = 22.922887 counts/FP

class L1aRawPixGenerate(object):
  '''This generates a L1A_RAW_PIX, L1A_BB, L1A_ENG and L1A_RAW_ATT
  files from a L0B input.'''
  def __init__(self, l0b, osp_dir, scene_file, run_config = None,
               build_id = "0.30",
               pge_version = "0.30", build_version="0100",
               file_version = "05"):
      '''Create a L1aRawPixGenerate to process the given L0 file. 
      To actually generate, execute the 'run' command.'''
      self.l0b = l0b
      self.osp_dir = osp_dir
      self.scene_file = scene_file
      self.run_config = run_config
      self.build_id = build_id
      self.pge_version = pge_version
      self.build_version = build_version
      self.file_version = file_version

  def process_scene_file(self):
    '''Process the scene file, returning the orbit, scene id, start, 
    and end times'''
    res = []
    with open(self.scene_file, "r") as fh:
      for ln in fh:
        orbit, scene_id, sc_start_time, sc_end_time = re.split(r'\s+',
                                                               ln.strip())
        orbit = int(orbit)
        scene_id = int(scene_id)
        ss = Time.parse_time(sc_start_time)
        se = Time.parse_time(sc_end_time)
        res.append([orbit, scene_id, ss, se])
    return res

  def locate_ev( self, idx, tot, codes, lid ): # Look for EV code in packets
    # Return EV0 of 0 or 1 indicates phase of mirror
    # EV0 = 2 if matching EV not found
    ev0 = 2
    while idx < tot:
      p1 = 0
      while p1 < FPPPKT and ev0 == 2:
        if int( float( lid[idx,p1] - codes[0] )/10.0 + 0.5 ) == 0: ev0 = 0
        elif int( float( lid[idx,p1] - codes[1] )/10.0 + 0.5 ) == 0: ev0 = 1
        else: p1 += 1
      if ev0 < 2:  # Found it
        print("Found PHASE %d EV=%d at %d in PKT %d" %(ev0,lid[idx,p1],p1,idx))
        return (idx,p1,ev0)
      else:  #  search next packet
        idx += 1
    return (idx,p1,ev0)

  def create_file(self, prod_type, orbit, scene, start_time, end_time,
                  primary_file = False, prod=True, intermediate=False):
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
    fname = ecostress_file_name(prod_type, orbit, scene, start_time,
                                build=self.build_version,
                                version=self.file_version,
                                intermediate=intermediate)
    if(primary_file):
        self.log_fname =  os.path.splitext(fname)[0] + ".log"
        self.log = open(self.log_fname, "w")
    fout = h5py.File(fname, "w", driver='core')
    m = WriteStandardMetadata(fout,
        product_specfic_group = prod_type + "Metadata",
        proc_lev_desc = 'Level 1A Raw Parameters',
        pge_name="L1A_RAW_PIX", local_granule_id=fname,
        build_id = self.build_id, pge_version= self.pge_version,
        orbit_based = (scene is None))
    if(self.run_config is not None):
        m.process_run_config_metadata(self.run_config)
    dt, tm = time_split(start_time)
    m.set("RangeBeginningDate", dt)
    m.set("RangeBeginningTime", tm)
    dt, tm = time_split(end_time)
    m.set("RangeEndingDate", dt)
    m.set("RangeEndingTime", tm)
    m.write()
    fout.close()
    return fname

  def run(self):

    ''' Do the actual generation of data.'''
    print("====  Start run ", datetime.now(), "  ====")
    self.log = None

    #  Read the PRT coefficients
    PRT = np.zeros( (17,3), dtype=np.float64 )
    with open( self.osp_dir+"/prt_coef.txt", "r") as pf:
      for i, pvl in enumerate( pf ):
        p0, p1, p2, p3 = re.split(r'\s+', pvl.strip())
        PRT[i,0] = float(p1)
        PRT[i,1] = float(p2)
        PRT[i,2] = float(p3)
        print("PRT[%d](%s) = %20.12f %20.12f %20.12f" % ( i, p0, PRT[i,0], PRT[i,1], PRT[i,2] ) )
    pf.close()

# PRT DN to Kelvin conversions

    p7r = np.poly1d([PRT[0,0], -(PRT[0,1]+PRT[0,2])] )
    prc = [n for n in range(5)]
    prh = [n for n in range(5)]
    prc[0] = np.poly1d([ PRT[1,2], PRT[1,1], PRT[1,0] ]) # PRT_313_T
    prc[1] = np.poly1d([ PRT[2,2], PRT[2,1], PRT[2,0] ]) # PRT_314_T
    prc[2] = np.poly1d([ PRT[4,2], PRT[4,1], PRT[4,0] ]) # PRT_317_T
    prc[3] = np.poly1d([ PRT[3,2], PRT[3,1], PRT[3,0] ]) # PRT_315_T
    prc[4] = np.poly1d([ PRT[5,2], PRT[5,1], PRT[5,0] ]) # PRT_318_T
    prh[0] = np.poly1d([ PRT[12,2], PRT[12,1], PRT[12,0] ]) # PRT_465_T
    prh[1] = np.poly1d([ PRT[13,2], PRT[13,1], PRT[13,0] ]) # PRT_466_T
    prh[2] = np.poly1d([ PRT[14,2], PRT[14,1], PRT[14,0] ]) # PRT_467_T
    prh[3] = np.poly1d([ PRT[15,2], PRT[15,1], PRT[15,0] ]) # PRT_468_T
    prh[4] = np.poly1d([ PRT[16,2], PRT[16,1], PRT[16,0] ]) # PRT_469_T

#  Get EV start codes for BB and IMG pixels
    ev_codes = np.zeros( (3,2), dtype=np.float32 )
    ' open EV codes file '
    with open( self.osp_dir + "/ev_codes.txt", "r") as ef:
        for i,evl in enumerate(ef):
            e0, e1, e2 = re.split(r'\s+', evl.strip())
            ev_codes[i,0] = float(e1)
            ev_codes[i,1] = float(e2)
            print("EV_CODES[%d](%s) = %f, %f" % (i,e0,ev_codes[i,0],
                                                 ev_codes[i,1] ))
    ef.close()

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

    #' initialize some output pointers for different bands '
    #pix_dat = [b for b in range(BANDS)]
    #b295 = [b for b in range(BANDS)]
    #b325 = [b for b in range(BANDS)]

    pkt_idx = 0

    pix_buf = np.zeros( ( PPFP, FPB3, BANDS ), dtype=np.uint16 )
    ev_buf = np.zeros( FPB3, dtype=np.uint32 )
    flex_buf = np.zeros( (FPPPKT, PPFP, BANDS), dtype=np.uint16 )

    o_start_time = None
    # iterate through scenes from scene start/stop file
    for orbit, scene_id, ss, se in self.process_scene_file():
      if o_start_time is None: o_start_time = ss
      o_end_time = se
      print("====  ", datetime.now(), "  ====")
      print("SCENE=%s START=%s END=%s SS=%f SE=%f" % ( scene_id, ss, se, ss.j2000, se.j2000 ) )

      good_pkt = 0
      good_bb = 0
      pkt_cnt = 0
      bb_cnt = 0

      ' search for packet containing scene start time '
      ' *** Account for actual time of camera switch-on from mirror angle *** '
      ' *** Account for missing packets, assume in time sequence *** '
      pktp0t = Time.time_gps(0.0)  # Initialize to GPS 0
      dt = float( int( ( pktp0t - ss )*100000.0 + 0.5 ) )
      while dt < 0.0 and pkt_idx<tot_pkts:
        gt = fswt[pkt_idx] + float(fpie_sync[pkt_idx] - fsw_sync[pkt_idx]) /1000000.0
        pktp0t = Time.time_gps(gt)
        dt = float( int( ( pktp0t - ss )*100000.0 + 0.5 ) )
        print("Packet %d ID=%d time=%f SS=%f DT=%f" % ( pkt_idx, pid[pkt_idx], pktp0t.j2000, ss.j2000, dt/100000.0 ) )
        pkt_idx += 1
      ' end searching for packet matching scene start time '
      if pkt_idx >= tot_pkts:
        print("Could not find Scene %s time %s (%fJ2K) in file %s PKT=%d" % ( scene_id, ss, ss.j2000, self.l0b, pkt_idx ) )
        return -1

      ' found scene start time in previous packet '
      if dt > 0.0: pkt_idx -= 2
      else: pkt_idx -= 1
      print("Found scene %s start time %f in packet[%d]=%d FP0 time=%f" % ( scene_id, ss.j2000, pkt_idx, pid[pkt_idx], pktp0t.j2000 ) )

      ' create datasets '
      ' Starting time of first focal plane in each scan '
      pix_time = []
      ' FPIE encoder value of each focal plane in scan '
      pix_ev = []
      ' Image and BB pixel dataset for each band '
      pix_dat = [ [ ] for i in range(BANDS)]
      b295 = [ [ ] for i in range(BANDS)]
      b325 = [ [ ] for i in range(BANDS)]

      # First focal plane frame of scene in current packet
      dt = pktp0t - ss
      p0 = int( dt/FP_DUR + 0.5 )
      ' loop through scans (256 lines/scan) in scene '
      line = 0  # line pointer in output image
      op = 0  # initialize output FP pointer
      pktp0t += SC_DUR
      scan = 0
      while scan < SCPS and pktp0t < se:
        pix_buf[:,:,:] = 0xffff  # pre-fill with null values
        ev_buf[:] = 0xffffffff
        # find matching encoder value
        p0,p1,ev0 = self.locate_ev( pkt_idx, tot_pkts, ev_codes[0,:], lid )
        if ev0 == 2:
          print("Could not find IMG EV SCENE=%s SCAN=%d IDX=%d P1=%d" % (scene_id, scan,p0,p1))
          break
        pkt_idx = p0
        if p0 == 0: pktid0 = 0
        else: pktid0 = pid[p0-1]
        if p1 > 0:  # calculate fswt for PKT
          if lid[p0,p1] < lid[p0,0]: p2 = lid[p0,p1]+MAX_FPIE-lid[p0,0]
          else: p2 = lid[p0,p1] - lid[p0,0]
          dt = float( p2 ) * CNT_DUR  # use EV in current PKT
          #dt = FP_DUR * float( p1-FPPPT )  # count backward from next PKT
          print("LID[%d,%d]%d - LID[%d,0]%d" %(p0,p1,lid[p0,p1],p0,lid[p0,0]))
          #p0 += 1
        else:  #  use time codes in current packet
          dt = 0.0
        gt = fswt[p0] + float(fpie_sync[p0] - fsw_sync[p0])/1000000.0 + dt
        pix_time.append(Time.time_gps( gt ).j2000)

        fpc = FPPPKT - p1
        idx_inc = 1
        skip = 0
        while op < FPB3:  # build up a full scan of IMG and BB pix
          if idx_inc == 1 and pkt_idx < tot_pkts:  #  read next packet
            flex_buf[:,:,:] = bip[pkt_idx,:,:,:]
            pktid = pid[pkt_idx]
            if pktid0 == 4294937295: skip = pktid * FPPPKT # 32 bit wrap
            else: skip = (pktid - pktid0 - 1) * FPPPKT
          if pkt_idx >= tot_pkts:
            print("End of file reached before end of scan=%d OP=%d" %(scan,op))
            flex_buf[:,:,:] = 0xffff
          # end reading new packet

# find starting EV for BB1, BB2, and IMG pixels
          print("SCENE=%s SCAN=%d LINE=%d DT=%f s2k=%f IDX=%d P1=%d OP=%d SKIP=%d FPC=%d" %(scene_id, scan, line, dt, pix_time[scan], pkt_idx, p1, op, skip, fpc))
          op += skip
          if op < FPB3:
            #print("transposing IDX=%d P1=%d FPC=%d OP=%d" % (pkt_idx, p1, fpc, op) )
            p0 = FPPSC - op
            if fpc > p0:
              fpc = p0  # runt at end of scan
              print("Last chunk: %d" % p0 )
            for b in range( BANDS ):  # copy packet data to pixel buffer
              pix_buf[:,op:op+fpc,b] = np.transpose(flex_buf[p1:p1+fpc,:,b])
            ev_buf[op:op+fpc] = lid[pkt_idx,p1:p1+fpc]  #  and current EVs
            op += fpc  #  next FP pointer in pix_buf
            if op == FPPSC:  # copy BB pixels
              # find cold BB pixels
              p0,p1,ev0 = self.locate_ev( pkt_idx, tot_pkts, ev_codes[1,:], lid)
              if ev0 == 2:
                print("Could not find CBB EV SCENE=%s SCAN=%d IDX=%d P1=%d"%(scene_id,scan,p0,p1))
                return -1
              print("Found CBB PKT=%d P1=%d PH=%d SCENE=%s SCAN=%d OP=%d" % (p0,p1,ev0,scene_id,scan,op))
              fpc = FPPPKT - p1
              pkt_idx = p0
              flex_buf[:fpc,:,:] = bip[pkt_idx,p1:,:,:]
              ev_buf[op:op+fpc] = lid[pkt_idx,p1:]
              pktid0 = pid[pkt_idx]
              pkt_idx += 1
              pktid = pid[pkt_idx]
              if p1>0:
                flex_buf[fpc:,:,:] = bip[pkt_idx,:p1,:,:]
                ev_buf[op+fpc:op+BBLEN] = lid[pkt_idx,:p1]
              for b in range(BANDS):
                pix_buf[:,op:op+BBLEN,b] = np.transpose(flex_buf[:BBLEN,:,b])
              bb_cnt += 1
              good_bb += 1
              op += BBLEN
              # find hot BB pixels
              p0,p1,ev0 = self.locate_ev( pkt_idx, tot_pkts, ev_codes[2,:], lid)
              if ev0 == 2:
                print("Could not find HBB EV SCENE=%s SCAN=%d IDX=%d P1=%d"%(scene_id,scan,p0,p1))
                return -1
              print("Found HBB PKT=%d P1=%d PH=%d SCENE=%s SCAN=%d OP=%d" % (p0,p1,ev0,scene_id,scan,op))
              fpc = FPPPKT - p1
              pkt_idx = p0
              flex_buf[:fpc,:,:] = bip[pkt_idx,p1:,:,:]
              ev_buf[op:op+fpc] = lid[pkt_idx,p1:]
              pktid0 = pid[pkt_idx]
              pkt_idx += 1
              pktid = pid[pkt_idx]
              if p1>0:
                flex_buf[fpc:,:,:] = bip[pkt_idx,:p1,:,:]
                ev_buf[op+fpc:op+BBLEN] = lid[pkt_idx,:p1]
              for b in range(BANDS):
                pix_buf[:,op:op+BBLEN,b] = np.transpose(flex_buf[:BBLEN,:,b])
              bb_cnt += 1
              good_bb += 1
              op += BBLEN
            #  end copying BB pixels

            p1 = 0  #  copy whole packets after the first (if partial)
            fpc = FPPPKT
            idx_inc = 1  #  normal packet increment
            if op<FPPSC:
              pktid0 = pid[pkt_idx]  #  save current packt ID
              pkt_idx += idx_inc
            pkt_cnt += 1
            good_pkt += 1
          else:  #  need to skip to future line
            print("flushing scan %d packet=%d OP=%d" % (scan, pkt_idx, op))
            idx_inc = 0  # do not read a new packet
            op = op + skip - FPB3
            if skip > 0:
              print("PKTID mismatch: Expected %d found %d" % (pktid0+1, pktid))
              pkt_cnt += skip/FPPPKT
              skip = 0
          # end copying or skipping pix_buf
        # end filling current pix_buf and ev_buf

        # copy to output file
        pix_ev.append(ev_buf[:FPPSC].copy())
        for b in range( BANDS ):
          pix_dat[b].append(pix_buf[:,0:FPPSC,b].copy())
          b295[b].append(pix_buf[:,FPPSC:FPPSC+BBLEN,b].copy())
          b325[b].append(pix_buf[:,FPPSC+BBLEN:FPB3,b].copy())
        op = 0
        line += PPFP
        pktp0t += SC_DUR
        scan += 1
        ' end copy image and BB pixels and EV for current scan '
      ' end scans loop '
      good_pkt -= 1
      pkt_cnt += int( float( (SCPS - scan) * FPB3 ) / 64.0 + 0.5 ) - 1
      if scan < SCPS: print("Total scans read  %d, padding" % scan )
      while scan < SCPS:  #  fill out incomplete scene with null values
        pix_buf[:,:,:] = 0xffff  # pre-fill with null values
        ev_buf[:] = 0xffffffff
        pix_ev.append(ev_buf[:FPPSC].copy())
        for b in range( BANDS ):
          pix_dat[b].append(pix_buf[:,0:FPPSC,b].copy())
          b295[b].append(pix_buf[:,FPPSC:FPPSC+BBLEN,b].copy())
          b325[b].append(pix_buf[:,FPPSC+BBLEN:FPB3,b].copy())
        scan += 1

      ' create scene file and image pixel, J2K, and FPIE ENC groups '
      pname = self.create_file( "L1A_RAW_PIX", orbit, scene_id, ss, se,
                                prod=False, intermediate=True)
      l1a_fp = h5py.File( pname, "r+", driver='core' )

      ' create BB file and BlackBodyPixels group '
      bname = self.create_file( "L1A_BB", orbit, scene_id, ss, se, prod=True )
      l1a_bp = h5py.File( bname, "r+", driver='core' )

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

      l1a_upg = l1a_fp.create_group("/UncalibratedPixels")
      l1a_ptg = l1a_fp.create_group("/Time")
      l1a_peg = l1a_fp.create_group("/FPIEencoder")
      l1a_bpg = l1a_bp.create_group("/BlackBodyPixels")
      pix_time=np.array(pix_time).repeat(256)
      t = l1a_ptg.create_dataset("line_start_time_j2000", data=pix_time,
                                 dtype="f8" )
      t.attrs["Description"] = "J2000 time of first pixel in line"
      t.attrs["Units"] = "second"
      t = l1a_peg.create_dataset("EncoderValue", data=np.array(pix_ev),
                                 dtype="u4" )
      for b in range( BANDS ):
        t = l1a_upg.create_dataset("pixel_data_%d" %(b+1),
                                   data=np.vstack(pix_dat[b]),
                                   chunks=(PPFP,FPPSC), dtype="u2" )
        t.attrs['Units']='dimensionless'
        t = l1a_bpg.create_dataset("B%d_blackbody_295K" %(b+1),
                                   data=np.vstack(b295[b]), chunks=(PPFP,BBLEN),
                                                  dtype="u2")
        t.attrs['Units']='dimensionless'
        t = l1a_bpg.create_dataset("B%d_blackbody_325K" %(b+1),
                                   data=np.vstack(b325[b]), chunks=(PPFP,BBLEN),
                                                  dtype="u2" )
        t.attrs['Units']='dimensionless'
      good_pkt = 0
      pkt_cnt = 0
      good_bb = 0
      bb_cnt = 0
    ' end scene loop '

    ' Read HK packets to build up ENG and raw ATT/EPH files '
    aqc = att.shape[0]

    ' create engineering file and datasets '
    print("crerating ENG and ATT files, AQC=%d" % aqc )
    feng = self.create_file( "L1A_ENG", orbit, None, o_start_time,
                             o_end_time, primary_file=True )
    eng = h5py.File( feng, "r+", driver='core' )
    epc = bbt.shape[0]
    eng_g = eng.create_group("/rtdBlackbodyGradients")
    rtd295 = eng_g.create_dataset("RTD_295K", shape=(epc,5), dtype='f4')
    rtd325 = eng_g.create_dataset("RTD_325K", shape=(epc,5), dtype='f4')
    rtdtime = eng_g.create_dataset("time_j2000", shape=(epc,2), dtype='f8')
    for i in range(epc):  # Convert DNs to Kelvin with PRT parameters
      for j in range( 5 ):
        dn = bbt[i,0,j]
        rtd295[i,j] = prc[j]( p7r( ( (dn>>8)&0xff) | ( (dn&0xff)<<8 ) ) )
        dn = bbt[i,1,j]
        rtd325[i,j] = prh[j]( p7r( ( (dn>>8)&0xff) | ( (dn&0xff)<<8 ) ) )
      rtdtime[i,0] = Time.time_gps( bb_time[i] ).j2000  # sample time
      rtdtime[i,1] = Time.time_gps( bb_fsw[i] ).j2000  # hk pkt time
    rtd295.attrs['Units']='K and XY'
    rtd325.attrs['Units']='K and XY'
    eng.close()

    print("====  ", datetime.now(), "  ====")
    ' create raw attitude/ephemeris file and datasets '
    fatt = self.create_file("L1A_RAW_ATT", orbit, None, o_start_time,
                            o_end_time, prod=False, intermediate=True)
    attf = h5py.File( fatt, "r+", driver='core' )
    att_g = attf.create_group("/Attitude")
    a2k = att_g.create_dataset("time_j2000", shape=(aqc,), dtype='f8' )
    q = att_g.create_dataset("quaternion", shape=(aqc,4), dtype='f8' )
    eph_g = attf.create_group("/Ephemeris")
    e2k = eph_g.create_dataset("time_j2000", shape=(aqc,), dtype='f8' )
    epos = eph_g.create_dataset("eci_position", shape=(aqc,3), dtype='f8' )
    evel = eph_g.create_dataset("eci_velocity", shape=(aqc,3), dtype='f8' )
    for i in range(aqc):
      a2k[i] = Time.time_gps( att_time[i] ).j2000 # sample time
      e2k[i] = Time.time_gps( att_fsw[i] ).j2000  # hk pkt time
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
