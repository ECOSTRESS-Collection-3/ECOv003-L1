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
#FP_DUR = 0.0000321982 - 1.2617745535714285714285714285714e-6
#FP_DUR = 0.0000321875 - 1.2510745535714285714285714285714e-6
FP_DUR = 0.0000321875
#FP_DUR = 0.00003180890736809696 # measured from test data 20170808
#FP_DUR = 0.0000322
#FP_DUR = 3.095533197239234e-5 - 1.9077034883720932e-8  # this is consistent with FOV of 25.475; = 24.475/(5400*6*RPM) - fudge
PKT_DUR = FP_DUR * float( FPPPKT )
IMG_DUR = FP_DUR * float( FPPSC )
PIX_DUR = FP_DUR * float( BBLEN*2 + FPPSC )
RPM = 25.4
MPER = 60.0/RPM # mirror period = 2.3622047 sec / rev
SCAN_DUR = MPER/2.0 # half-mirror rotation = 1.1811024 sec
FP_ANG = FP_DUR*RPM*6.0 # FP angle = .0047175926 deg / FP
FOV = FP_DUR*RPM*6.0*FPPSC # field of view = 25.475000 deg / scan
ANG1 = FOV / 2.0
ANG0 = -ANG1
ANG2 = float( int( (ANG1 + FP_ANG*float(BBLEN*2))*1000.0 ) )/1000.0
# FPIE mirror encoder - 50.95 degree swath width
# covered by 25.475 degree of mirror scan.  Mirror
# is 2-sided, so every other scan is 180 degrees apart
MAX_FPIE=1749248
EV_DUR = 60.0/RPM/float( MAX_FPIE )  # = 1.3504 microsecond/count
#EV_DUR = 60.0/RPM/float( MAX_FPIE ) - 1.357079461852133e-10  # = 1.3504 microsecond/count - fudge factor
#EV_DUR = 1.3505012369820937e-06 # measured from test data 20170803
ANG_INC = 360.0 / float( MAX_FPIE )  # = 0.00020580272 deg/count
FP_EV = FP_DUR*RPM*MAX_FPIE/60.0 + .004260048 # = 23.835326 counts/FP
PKT_EV = FP_DUR*RPM*MAX_FPIE*FPPPKT/60.0 # = 1525.460873 counts/PKT
IMG_EV = FP_DUR*RPM*MAX_FPIE*FPPSC/60.0 # = 128710.76112 counts/IMG
FP_TOL = 3
SCENE_DUR = SCAN_DUR * SCPS

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
        e0, e1, e2, e3 = re.split(r'\s+', pvl.strip())
        PRT[i,0] = float(e1)
        PRT[i,1] = float(e2)
        PRT[i,2] = float(e3)
        print("PRT[%d](%s) = %20.12f %20.12f %20.12f" % ( i, e0, PRT[i,0], PRT[i,1], PRT[i,2] ) )
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
    ev_codes = np.zeros( (4,6), dtype=np.int32 )
    ev_names = [ e0 for e0 in range(4) ]
    ' open EV codes file '
    with open( self.osp_dir + "/ev_codes.txt", "r") as ef:
      for i,evl in enumerate(ef):
        e0, e1, e2, e3, e4 = re.split(r'\s+', evl.strip())
        ev_names[i] = e0
        if int(e2) < int(e1): # compensate for zero-crossing in EV range
          ev_codes[i,4] = MAX_FPIE - int(e1) # delta to end
          ev_codes[i,0] = 0 # new start EV to search
          ev_codes[i,1] = int(e2) + ev_codes[i,4] # new end EV
        else:
          ev_codes[i,4] = 0
          ev_codes[i,0] = int(e1)
          ev_codes[i,1] = int(e2)
        if int(e4) < int(e3): # compensate for zero-crossing in EV range
          ev_codes[i,5] = MAX_FPIE - int(e3) # delta to end
          ev_codes[i,2] = 0 # new start EV to search
          ev_codes[i,3] = int(e4) + ev_codes[i,5] # new end EV
        else:
          ev_codes[i,5] = 0
          ev_codes[i,2] = int(e3)
          ev_codes[i,3] = int(e4)
        print("P1=%d P2=%d P3=%d P4=%d"%(int(e1),int(e2),int(e3),int(e4)))
        print("EV_CODES[%d](%s) = (%d,%d) (%d,%d) (%d,%d)" % (i,ev_names[i],
                                ev_codes[i,0],ev_codes[i,1],ev_codes[i,2],
                                ev_codes[i,3],ev_codes[i,4],ev_codes[i,5] ))
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

    epc = bb_time.shape[0]
    bbtime = np.zeros( epc, dtype=np.float64 )
    bbtime[:] = bb_time[:]
    bbfsw = np.zeros( epc, dtype=np.float64 )
    bbfsw[:] = bb_fsw[:]

    tot_pkts = bip.shape[0]
    print("Opened L0B file %s, TOT_PKTS=%d" % (self.l0b, tot_pkts ) )

    # calculate FSW times of each packet (GPS times)
    gpt = np.zeros( tot_pkts, dtype=np.float64 )
    gpt[:] = fswt[:] + ( fpie_sync[:] - fsw_sync[:] ) / 1000000.0

    # extract encoder values
    i,j = lid.shape
    lev = np.zeros( (i,j), dtype=np.uint32 )
    lev[:,:] = lid[:,:]&0x1fffff

    # working array
    flex_buf = np.zeros( (PPFP, FPPPKT, BANDS), dtype=np.uint16 )
    # output file arrays
    img = np.zeros( ( SCPS*PPFP, FPPSC, BANDS ), dtype=np.uint16 )
    hbb = np.zeros( ( SCPS*PPFP, BBLEN, BANDS ), dtype=np.uint16 )
    cbb = np.zeros( ( SCPS*PPFP, BBLEN, BANDS ), dtype=np.uint16 )
    pix_time = np.zeros( SCPS*PPFP, dtype=np.float64 )
    ev_buf = np.zeros( (SCPS, FPPSC), dtype=np.uint32 )
    buf = [0,1,2]
    buf[0] = hbb
    buf[1] = cbb
    buf[2] = img

    cnt = np.zeros( 3, dtype=np.float32 )
    good = np.zeros( 3, dtype=np.float32 )
    st = np.zeros( 3, dtype=np.float64 )

    pkt_idx = 0 # start looking at first packet in file
    o_start_time = None
    # iterate through scenes from scene start/stop file
    for orbit, scene_id, ss, se in self.process_scene_file():
      if o_start_time is None: o_start_time = ss
      o_end_time = se
      print("====  ", datetime.now(), "  ====")
      print("SCENE=%s START=%s END=%s SS=%f SE=%f" % ( scene_id, ss, se, ss.j2000, se.j2000 ) )

      good[:] = 0.0
      cnt[:] = 0.0
      miss = 0

      #*** Account for missing packets, assume packets in time sequence ***
      ' search for packet containing scene start time '
      pktp0t = Time.time_gps( gpt[pkt_idx] )
      dt = float( int( (pktp0t - ss)*100000.0 + 0.5 ) )
      while dt < 0.0 and pkt_idx<tot_pkts:
        gt = gpt[pkt_idx]
        pktp0t = Time.time_gps(gt)
        dt = float( int( (pktp0t - ss)*100000.0 + 0.5 ) )
        print("Packet %d ID=%d time=%f SS=%f DT=%f" % ( pkt_idx, pid[pkt_idx], pktp0t.j2000, ss.j2000, dt/100000.0 ) )
        pkt_idx += 1
      ' end searching for packet matching scene start time '
      if pkt_idx >= tot_pkts:
        print("Could not find Scene %s time %s (%fJ2K) in file %s PKT=%d" % ( scene_id, str(ss), ss.j2000, self.l0b, pkt_idx ) )
        return -1

      ' found scene start time in previous packet '
      if dt > 0.0: pkt_idx -= 1
      print("Located scene %s start time %f in PKT[%d] J2K=%f %s" % ( scene_id, ss.j2000, pkt_idx, pktp0t.j2000, str(pktp0t) ) )

      # initialize buffers to fill values
      img[ : ] = 0xffff
      hbb[ : ] = 0xffff
      cbb[ : ] = 0xffff
      pix_time[ : ] = 0.0
      ev_buf[ : ] = 0xffffffff

      line = 0  # line pointer in output image
      op = 0  # initialize output FP pointer
      pktp0t += PIX_DUR  # point to end of BB and IMG pixels

      scan = 0
      scans = 0
      if pkt_idx > 0: pkt_idx -= 1 # compensate for time code error
      st[0] = gpt[pkt_idx] # initial start time for first scan
      while scan < SCPS and pktp0t < se:

        #  Loop through pixel sequences in scan
        cont = 1
        s0 = scan
        line = scan * PPFP
        st[2] = 0
        for seq in range( 3 ):
          op0 = ev_codes[3,seq]
          op1 = ev_codes[3,seq+1]
          e0 = pkt_idx
          e2 = 2
          while e0 < tot_pkts and e2 == 2:
            if gpt[e0] > se.gps:
              print("Past scene end time seeking %s IDX=%d" %(ev_names[seq],e0))
              scan = SCPS # end current scene
              pkt_idx = e0
              cont = 0
              break # exit seek loop
            elif gpt[e0]-st[0] > SCAN_DUR and seq > 0:
              print("Past scan end time seeking %s IDX-%d" %(ev_names[seq],e0))
              scan = int( (gpt[e0] - ss.gps)/SCAN_DUR + 0.999) # new scan
              pkt_idx = e0
              cont = 0
              break # exit seek loop
            # find start of sequence and mirror phase
            e1 = 0
            while e1 < FPPPKT and e2 == 2:
              lid0 = ( lev[e0,e1] + ev_codes[seq,4] ) % MAX_FPIE
              lid1 = ( lev[e0,e1] + ev_codes[seq,5] ) % MAX_FPIE
              if lid0 >= ev_codes[seq,0] and lid0 <= ev_codes[seq,1]: e2 = 0
              elif lid1 >= ev_codes[seq,2] and lid1 <= ev_codes[seq,3]: e2 = 1
              else: e1 += 1 # lookat next EV
            if e2 == 2:  e0 += 1 # look in next packet
          pkt_idx = e0

          if cont==0 or e0>=tot_pkts:
            if e0>=tot_pkts: # hit EOF
              print("%s EV not found SCENE=%s IDX=%d P1=%d" %(ev_names[seq],scene_id,e0,e1))
              e0 = tot_pkts - 1
              e1 = FPPPKT - 1
              scan = SCPS
            else:
              print("Next scene")
              op = op1
            break # exit seq loop

          # calculate fswt for first FP in SEQ
          if e1 == 0:
            st[seq] = gpt[e0]
          else:
            dt = ( (int(lev[e0,e1]) - int(lev[e0,0]))%MAX_FPIE ) * EV_DUR
            t0 = gpt[e0-1] + dt + PKT_DUR ### time code error
            t1 = gpt[e0+1] + (e1 - FPPPKT) * FP_DUR # from next pkt
            if t1 - t0 > SCAN_DUR: st[seq] = t1
            else: st[seq] = t0
          if seq==2:
            pix_time[line] = Time.time_gps( st[2] ).j2000
            pix_time[line+1:line+PPFP] = pix_time[line]
          print("Found %s LID[%d,%d]=%d PH=%d SCENE=%s SCAN=%d OP=%d GP=%f %s"%(ev_names[seq],e0,e1,lev[e0,e1],e2,scene_id,scan,op,Time.time_gps(st[seq]).j2000,str(Time.time_gps(st[seq]))))
  
          # Copy pixels from PKT
          p1 = e1
          fpc = FPPPKT - p1  # FPs to copy from first PKT
          while op < op1 and e0 < tot_pkts:
            #print("SCENE=%d SCAN=%d E0=%d E1=%d ST=%f GPT=%f" %(scene_id,scan,e0,e1,st[0],gpt[e0]))
            gs = seq
            if gpt[e0] > se.gps:
              print("GPT %f past SE %f copying %s IDX=%d" %(gpt[e0],se.gps,ev_names[seq],e0))
              scan = SCPS # force new scene
              pkt_idx = e0 + 1
              seq = 3
              cont = 0
              break # exit sequence copy loop
            if gpt[e0]-st[0] > SCAN_DUR:
              print("GPT %f past scan end %f copying %s IDX=%d" %(gpt[e0],st[0]+SCAN_DUR,ev_names[seq],e0))
              scan = int( (gpt[e0] - ss.gps)/SCAN_DUR +0.5 ) # new scan
              pkt_idx = e0 + 1
              seq = 3
              cont = 0
              break # exit sequence copy loop
  
            for b in range( BANDS ): # transpose new packet to flex_buf
              flex_buf[:,:,b] = np.transpose(bip[e0,:,:,b])
            e3 = op1 - op
            if fpc > e3:
              fpc = e3  # runt at end of sequence
              print("Last %s chunk:%d IDX=%d" %(ev_names[seq],e3,pkt_idx) )
            dp = op - op0
            #print("SEQ=%d LINE=%d DP=%d P1=%d FPC=%d" %(seq,line,dp,p1,fpc))
            buf[seq][line:line+PPFP,dp:dp+fpc,:] = flex_buf[:,p1:p1+fpc,:]
            if seq==2: ev_buf[scan,dp:dp+fpc] = lev[pkt_idx,p1:p1+fpc]
            op += fpc  #  next FP pointer in pix_buf
            fpc = FPPPKT # full PKTs after (partial) first PKT
            p1 = 0
            e0 += 1
            #cnt[seq] += 1.0
            good[seq] += 1.0
            # end copying current PKT
          # end seq copy loop
          pkt_idx = e0 - 1 # back up 1 packet for next seek
          if e1 > 0:
            #cnt[seq] -= 1
            good[gs] -= 1
        # end seq loop

        if s0<SCPS:
          print("SCENE=%s SCAN=%d LINE=%d DT=%f s2k=%f IDX=%d P1=%d OP=%d P0T=%f"%(scene_id,s0,line,dt,pix_time[s0],pkt_idx,e1,op,pktp0t.j2000))
          if scan>=SCPS:
            print("Forced to next scene IDX=%d E1=%d OP=%d" %(pkt_idx,e1,op) )
            scans += 1
          elif scan>s0:
            print("Forced to next scan %d IDX=%d E1=%d OP=%d" %(scan,pkt_idx,e1,op) )
            scans += 1

        op = 0
        if cont==1:
          pktp0t += SCAN_DUR
          scans += 1
          scan += 1
      # end scan loop

      #bb_cnt = cnt[0] + cnt[1]
      bb_cnt = scans*2
      good_bb = good[0] + good[1]
      #pkt_cnt = cnt[2]
      pkt_cnt = int( float( scans*FPPSC ) / 64.0 + 0.5 )
      good_pkt = good[2]

      # copy to output files

      ' create scene file and image pixel, J2K, and FPIE EV groups '
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
      print("SCENE %s completed, SCANS=%d (%f) %d / %d GOOD/IMG, (%f) %d / %d GOOD/BB" % ( scene_id, scans, pcomp, good_pkt, pkt_cnt, bcomp, good_bb, bb_cnt ))

      l1a_upg = l1a_fp.create_group("/UncalibratedPixels")
      l1a_ptg = l1a_fp.create_group("/Time")
      l1a_peg = l1a_fp.create_group("/FPIEencoder")
      l1a_bpg = l1a_bp.create_group("/BlackBodyPixels")
      l1a_rtg = l1a_bp.create_group("/rtdBlackbodyGradients")
      #pix_time=np.array(pix_time).repeat(256)
      t = l1a_ptg.create_dataset("line_start_time_j2000", data=pix_time,
                                 dtype="f8" )
      t.attrs["Description"] = "J2000 time of first pixel in line"
      t.attrs["Units"] = "second"
      t = l1a_peg.create_dataset("EncoderValue", data=ev_buf, dtype="u4" )

      e0, e1, e2 = img.shape
      print("Writing file %s size=%d %d %d BANDS=%d" %( pname, e0, e1, e2, BANDS ) )
      for b in range( BANDS ):
        t = l1a_upg.create_dataset("pixel_data_%d" %(b+1),
                                   data=img[:,:,b],
                                   chunks=(PPFP,FPPSC), dtype="u2" )
        t.attrs['Units']='dimensionless'
        t = l1a_bpg.create_dataset("B%d_blackbody_295K" %(b+1),
                                   data=cbb[:,:,b], chunks=(PPFP,BBLEN),
                                                  dtype="u2")
        t.attrs['Units']='dimensionless'
        t = l1a_bpg.create_dataset("B%d_blackbody_325K" %(b+1),
                                   data=hbb[:,:,b], chunks=(PPFP,BBLEN),
                                                  dtype="u2" )
        t.attrs['Units']='dimensionless'

      # copy RTD temps to BB file
      p0 = np.argmax( bbtime >= ss.gps )
      p1 = np.argmax( bbtime >= se.gps )
      print("Copying RTD for SCENE %d P0=%d P1=%d" %(scene_id, p0, p1))
      bt=l1a_rtg.create_dataset("time_j2000", shape=(p1-p0+1,), dtype='f8')
      r2=l1a_rtg.create_dataset("RTD_295K", shape=(p1-p0+1,5,), dtype='f4')
      r3=l1a_rtg.create_dataset("RTD_325K", shape=(p1-p0+1,5,), dtype='f4')
      for i in range( p0, p1+1 ):
        bt[i-p0] = Time.time_gps( bbtime[i] ).j2000
        for j in range( 5 ):
          r2[i-p0,j] = prc[j]( p7r( bbt[i,0,j] ) ) + 273.15
          r3[i-p0,j] = prh[j]( p7r( bbt[i,1,j] ) ) + 273.15

    ' end scene loop '

    ' create engineering file and datasets '
    print("creating ENG file, EPC=%d" % epc )
    feng = self.create_file( "L1A_ENG", orbit, None, o_start_time,
                             o_end_time, primary_file=True )
    eng = h5py.File( feng, "r+", driver='core' )
    eng_g = eng.create_group("/rtdBlackbodyGradients")
    rtd295 = eng_g.create_dataset("RTD_295K", shape=(epc,5), dtype='f4')
    rtd325 = eng_g.create_dataset("RTD_325K", shape=(epc,5), dtype='f4')
    rtdtime = eng_g.create_dataset("time_j2000", shape=(epc,2), dtype='f8')
    for i in range(epc):  # Convert DNs to Kelvin with PRT parameters
      for j in range( 5 ):
        rtd295[i,j] = prc[j]( p7r( bbt[i,0,j] ) ) + 273.15
        rtd325[i,j] = prh[j]( p7r( bbt[i,1,j] ) ) + 273.15
      rtdtime[i,0] = Time.time_gps( bbtime[i] ).j2000  # sample time
      rtdtime[i,1] = Time.time_gps( bbfsw[i] ).j2000  # hk pkt time
    rtd295.attrs['Units']='K and XY'
    rtd325.attrs['Units']='K and XY'

    ' create raw attitude/ephemeris file and datasets '
    aqc = att.shape[0]
    print("creating raw ATT file, AQC=%d" % aqc )
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
    q.attrs['Description']='Attitude quaternion, goes from spacecraft to ECI. The coefficient convention used has the real part in the first column.'
    q.attrs['Units']='dimensionless'
    epos[:,:] = pos[:,:]
    epos.attrs['Description']='ECI position'
    epos.attrs['Units']='m'
    evel[:,:] = vel[:,:]
    evel.attrs['Description']='ECI velocity'
    evel.attrs['Units']='m/s'
    attf.close()

    # Write out a dummy log file
    eng.close()
    print("This is a dummy log file", file = self.log)
    self.log.flush()
    print("====  End run ", datetime.now(), "  ====")
