# Scan L0B file to locate starts of image scenes and scancs
import h5py
#import shutil
import re, sys, os
#from .write_standard_metadata import WriteStandardMetadata
#from .misc import ecostress_file_name
from geocal import Time
import numpy as np
import struct

' short word offsets into FPIE packet array '

' packet primary header '
HSYNC = 0
PKTID = HSYNC + 2
ENCOD = PKTID + 2
ISTATE = ENCOD + 128
FTIME = ISTATE + 2
DTIME = FTIME + 4
DSYNC = DTIME + 4
HSUM = 282
HDR_LEN = 284
DSUM = 98588
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

#FP_DUR = 0.0000321982 - 1.2617745535714285714285714285714e-6
#FP_DUR = 0.0000321982
FP_DUR = 0.0000321875
#FP_DUR = 0.0000322
#FP_DUR = 3.095533197239234e-5 - 1.9077034883720932e-8  # this is consistent with FOV of 25.475; = 24.475/(5400*6*RPM) - fudge
PKT_DUR = FP_DUR * float( FPPPKT )  # 0.00197993123 sec / pkt
IMG_DUR = FP_DUR * float( FPPSC )
PIX_DUR = FP_DUR * float( BBLEN*2 + FPPSC )
RPM = 25.4
MPER = 60.0/RPM # mirror period = 2.3622047 sec / rev
SCAN_DUR = MPER/2.0 # half-mirror rotation = 1.1811024 sec
FP_ANG = FP_DUR*RPM*6.0 # FP angle = 0.00471471124 deg / FP
FOV = FP_DUR*RPM*6.0*FPPSC # field of view = 25.459440685 deg / scan

MAX_FPIE=1749248
#EV_DUR = 60.0/RPM/float( MAX_FPIE ) - 1.357079461852133e-10  # = 1.3504 microsecond/count
EV_DUR = 60.0/RPM/float( MAX_FPIE ) # = 1.35041156 microsecond/count
#EV_DUR = 1.3505012369820937e-06 # measured from data 20170803
FP_EV = FP_DUR*RPM*MAX_FPIE / 60.0 # = 23.835326 counts/FP
PKT_EV = FP_DUR*RPM*MAX_FPIE*FPPPKT/60.0 # = 1525.460873 counts/PKT
IMG_EV = FP_DUR*RPM*MAX_FPIE*FPPSC/60.0 # = 128710.76112 counts/IMG
FP_TOL = 3

SCENE_DUR = SCAN_DUR * SCPS

def l0b_scan():
  args = len(sys.argv)
  if( args <= 1 ):
    print("Usage: python l0b_scan L0B_FILE_NAME [OSP_DIR] [OUT_DIR] [SP] [OFF] [EP]")
    exit()
  else:
    l0b_name = sys.argv[1]
  m=re.search('L0B_(.+?)_',l0b_name)
  if m:
    onum = m.group(1)
    print("Orbit=%s" % onum )
  else:
    print("Could not find orbit number from L0B file name %s" %l0b_name)
  bname = os.path.basename(l0b_name)
  if args > 2: osp_dir = sys.argv[2]
  else: osp_dir = './'
 
  if args > 3: out_dir = sys.argv[3]
  else: out_dir = './'
 
  if args > 4: pkts = int( sys.argv[4])  # starting packet
  else: pkts = 0
  if pkts < 0: pkts = 0
  
  if args > 5: poff = int( sys.argv[5] )  # packet offset
  else: poff = 0
  
  if args > 6: pkte = int( sys.argv[6] )  # ending packet
  else: pkte = -1
  
  fin = h5py.File(l0b_name,"r", driver='core')
  bip = fin["/flex/bip"]
  lid = fin["/flex/id_line"]
  pid = fin["/flex/id_packet"]
  fswt = fin["/flex/time_fsw"]
  fsws = fin["/flex/time_sync_fsw"]
  fpies = fin["/flex/time_sync_fpie"]
  bbt = fin["hk/status/temperature"]
  hst=fin['hk/status/time']
  hss=fin['hk/status/time_fsw']
  
  tot_pkts, fpppkt, ppfp, bands = bip.shape
  if pkte == -1: pkte = tot_pkts
  print("Opened L0B file %s TOT_PKTS=%d fpppkt=%d ppfp=%d bands=%d" % (l0b_name, tot_pkts, fpppkt, ppfp, bands ) )

  i,j=lid.shape
  lev = np.zeros( (i,j), dtype=np.uint32 )
  lev[:,:] = lid[:,:] & 0x1fffff

  # calculate GPS times of each packet
  gpt = np.zeros( tot_pkts, dtype=np.float64 )
  gpt[:] = fswt[:] + fpies[:]/1000000.0 - fsws[:]/1000000.0
  
  #  Get EV start codes for BB and IMG pixels
  ev_codes = np.zeros( (4,6), dtype=np.int32 )
  ev_names = [ e0 for e0 in range(4) ]
  ' open EV codes file '
  with open( osp_dir+"ev_codes.txt", "r") as ef:
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
  
  '''
  PRT = np.zeros( (17,3), dtype=np.float64 )
  with open( osp_dir+"prt_coef.txt", "r") as pf:
    for i, pvl in enumerate( pf ):
      p0, p1, p2, p3 = re.split(r'\s+', pvl.strip())
      PRT[i,0] = float(p1)
      PRT[i,1] = float(p2)
      PRT[i,2] = float(p3)
      print("PRT[%d](%s) = %20.12f %20.12f %20.12f" % ( i, p0, PRT[i,0], PRT[i,1], PRT[i,2] ) )
  pf.close()
  
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
  
  epc = bbt.shape[0]
  for i in range( 10 ):  # print out some BB temps
    print("hk/status/time(%d)=%f hk/status/time_fsw=%f" %(i,hst[i],hss[i]) )
    print("BBT(%3d)=" % i, end="" )
    for j in range( 5 ):
      d2 = bbt[i,0,j]
      d3 = bbt[i,1,j]
      t2 = prc[j]( p7r( d2 ) ) + 273.15
      t3 = prc[j]( p7r( d3 ) ) + 273.15
      print(" %8.3f(%d),%8.3f(%d)" %(t2,d2,t3,d3), end="")
    print("")
  '''
  
  ev0 = 0
  scenes = []
  sid = 0
  scans = 0
  idx = pkts
  t0 = gpt[pkts] # time of first packet
  while idx < pkte:
    ss = []
    cont = 1
    for seq in range( 3 ): # Look for starting EV of sequences
      # seek to start of sequence
      e0 = idx
      e2 = 2
      while e0 < pkte and e2 == 2:
        dt = gpt[e0] - t0
        t0 = gpt[e0]
        if dt > SCAN_DUR and seq > 0:
          print("Discontinuity seeking %s IDX=%d" %(ev_names[seq],e0))
          cont = 0
          break # stop seeking current sequence, skip current scan
        e1 = 0
        while e1 < FPPPKT and e2 == 2:
          lid0 = ( lev[e0,e1] + ev_codes[seq,4] ) % MAX_FPIE
          lid1 = ( lev[e0,e1] + ev_codes[seq,5] ) % MAX_FPIE
          if lid0 >= ev_codes[seq,0] and lid0 <= ev_codes[seq,1]: e2 = 0
          elif lid1 >= ev_codes[seq,2] and lid1 <= ev_codes[seq,3]: e2 = 1
          else: e1 += 1 # lookat next EV
        if e2 == 2:  e0 += 1 # look in next packet
      idx = e0
      if cont==0 or e0 >=pkte:
        if e0 >= pkte: print("Starting %s packet not found in file, IDX=%d terminating" %( ev_names[seq], e0 ))
        cont = 0
        break # get out of sequence loop

      if e1>0: # calculate SEQ start time from next packet
        p0 = e0 + 1
        dt = (e1 - FPPPKT) * FP_DUR
      else:
        p0 = e0
        dt = 0
      ss.append( gpt[p0]+dt )
      if ss[seq] - ss[0] > SCAN_DUR:
        print("Discontinuity at IDX=%d in %s" %(e0,ev_names[seq]))
        cont = 0
        break
      print("Found %s LID[%d,%d]=%d PH=%d SCENE=%d SCAN=%d T2K=%f %s" %(ev_names[seq], e0, e1, lev[e0,e1], e2, sid+1, scans+1, Time.time_gps(ss[seq]).j2000, str(Time.time_gps(ss[seq])) ))

    if cont == 1: # continue collecting scans in scene
      if scans==0:
        sss = str( Time.time_gps( ss[0] ) )[:26] # UTC of scene start time
        sst = ss[0] # save scene start time
        sse = sst + SCENE_DUR # estimate scene end time
      scans += 1
      se = ss[2] + IMG_DUR + FP_DUR # estimate IMG end time
      p0 = np.argmax( gpt>se ) # find packet exceeding end time
      if p0 == 0: # hit EOF
        idx = pkte
        sse = se - 1
        p0 = pkte - 1
      else:
        idx = p0
      dt = se - gpt[p0-1] - PKT_DUR # account for time code error
      p1 = int(dt / FP_DUR+0.5)
      if p1 >= FPPPKT or gpt[p0] - gpt[p0-1] > SCAN_DUR: # short IMG seq
        se = gpt[p0-1] + PKT_DUR - FP_DUR # set to end of previous packet
        if idx == pkte: se += PKT_DUR # at EOF
        sse = se - 1 # force new scene
      else: se = gpt[p0-1] + PKT_DUR + FP_DUR*p1 # refine end time
      print("IMG ends at P0=%d P1=%d SE=%f T2K=%f DT=%f" %(p0,p1,se,Time.time_gps(se).j2000,dt) )

    else: # skip discontinuity and force new scene
      #se = ss[0]
      sse = se - 1
    print("SCANS=%d P0=%d P1=%d GPT=%f SSE=%f se=%f" %( scans, p0, p1, gpt[p0], sse, se ) )
    if scans==SCPS or sse < se: # record current scene
      sid += 1
      ses = str( Time.time_gps( se ) )[:26]
      ote = ss[0] + SCAN_DUR # save scan end time as orbit end time
      scenes.append("%5s	%03d	%s	%s\n" %( onum, sid, sss, ses ))
      print("New scene ID=%d SCANS=%d %s" %(sid, scans, scenes[sid-1]))
      scans = 0

  # write scene file
  sss = bname[10:25]
  ses = str( Time.time_gps( ote ) )
  sf = "Scene_%5s_%s_%s.txt" % ( onum, sss, ses[0:4]+ses[5:7]+ses[8:13]+ses[14:16]+ses[17:19])
  print("%s" %sf )
  sfd = open( out_dir+sf, "w" )
  for i in range( sid ): sfd.write(scenes[i])
  sfd.close()

l0b_scan()
