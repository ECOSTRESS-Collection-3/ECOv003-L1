import h5py
import shutil
import re
import os
import glob
import numpy as np
from .write_standard_metadata import WriteStandardMetadata
from .misc import ecostress_file_name, time_split
import ecostress
import geocal
from geocal import Time
import sys
from datetime import datetime
from datetime import timedelta

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
'''

' number of pixels per focal plane '
PPFP = 256
' number of focal planes per full scan '
#FPPSC = 5400
' number of FPs in each BB per scan '
BBLEN = 64
' Total FPs per scan including hot and cold BB '
#FPB3 = FPPSC + BBLEN*2
' number of FPs per raw packet '
FPPPKT = 64
' Scans per scene '
SCPS = 44
' lines per scene '
LPS = PPFP * SCPS
' standard packets per scene rounded up '
#PPSC = int( (SCPS*FPB3+FPPPKT-1) / FPPPKT )


class L1aRawPixGenerate(object):
  '''This generates a L1A_RAW_PIX, L1A_BB, L1A_ENG and L1A_RAW_ATT
  files from a L0B input.'''
  def __init__(self, l0b, obst_dir, osp_dir, scene_file, run_config = None,
               collection_label = "ECOSTRESS",
               build_id = "0116",
               pge_version = "0.50", 
               file_version = "01"):
      '''Create a L1aRawPixGenerate to process the given L0 file. 
      To actually generate, execute the 'run' command.'''
      self.l0b = l0b
      self.obst_dir = obst_dir
      self.osp_dir = osp_dir
      self.scene_file = scene_file
      self.run_config = run_config
      self.collection_label = collection_label
      self.build_id = build_id
      self.pge_version = pge_version
      self.file_version = file_version
      self.collection_label = collection_label

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
        sts = Time.parse_time(sc_start_time)
        ste = Time.parse_time(sc_end_time)
        res.append([orbit, scene_id, sts, ste])
    return res

  def create_file(self, prod_type, orbit, scene, start_time, end_time,
                  primary_file = False, prod=True, intermediate=False):
    '''Create the file, generate the standard metadata, and return
    the file handle and metadata handle.'''

    fname = ecostress_file_name(prod_type, orbit, scene, start_time,
                                collection_label = self.collection_label,
                                build=self.build_id,
                                version=self.file_version,
                                intermediate=intermediate)
    #if(primary_file):
    #    self.log_fname =  os.path.splitext(fname)[0] + ".log"
    #    self.log = open(self.log_fname, "w")
    fout = h5py.File(fname, "w", driver='core')
    m = WriteStandardMetadata(fout,
        product_specfic_group = prod_type + "Metadata",
        proc_lev_desc = 'Level 1A Raw Parameters',
        pge_name="L1A_RAW_PIX", local_granule_id=fname,
        collection_label = self.collection_label,                      
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
    m.set_input_pointer([self.l0b, self.scene_file])
    return fout, m, fname

  def detect_obst( self, sts, ste ):
    # look for dolar array obstruction on scene using start/end times
    # and solar array obstruction reports from HOSC

      ys = str( sts )[0:4]
      path=self.obst_dir
      obst_files=path+"ECO*Obst."+ys
      print('STS=%s STE=%s' %( str(sts), str(ste) ) )
      print('OBSTFILES=%s' %obst_files )
      fov_obst = "NO"
      for file_name in glob.glob(obst_files):
        fn = os.path.basename( file_name )
        pre,doy1,doy2,post,year=re.split('\_|\.',fn)
        d1 = year + '::' + doy1
        yr = int(year)
        if int( doy2 ) < int( doy1 ) : yr = yr + 1
        year2 = str(yr)
        d2 = year2 + '::' + doy2
        t1 = Time.parse_time( d1 )
        t2 = Time.parse_time( d2 )
        ## print("ObstFile dates=%s %s" %( d1, d2 ) )
        if ste<t1 : break  #  time codes beyond scene end
        if sts>t2 :  #  time codes before scene start
          continue
        print('Found file %s' %file_name )
        with open( file_name, 'r' ) as ifd:
          for lbuf in ifd:
            if 'OBSTRUCTED' not in lbuf:  #  Look for "OBSTRUCTED"
              continue
            a,b,c,doy1,t1,d,doy2,t2 = re.split(' |\,|\/', lbuf )
            #print("OBST lbuf %s %s %s" %(lbuf,t1,t2))
            d1 = year + '::' + doy1 + ' ' + t1
            d2 = year2 + '::' + doy2 + ' ' + t2[0:8]
            t1=Time.parse_time( d1 )
            t2=Time.parse_time( d2 )
            if ste<t1 : break  #  time codes beyond scene end
            if sts>t2 :  #  time codes before scene start
              continue
            print("Found OBST times %s %s" %( t1, t2 ) )
            print("Found OBST scene %s %s" %( sts, ste ) )
            fov_obst = "YES"
            break
        print("Close file %s" %file_name )
        ifd.close()
        if fov_obst != "NO" : break
      return fov_obst

  def run(self):

    ''' Do the actual generation of data.'''
    print("====  Start run ", datetime.now(), "  ====")
    self.log = None

#  setup for locating scene corners
    sys.path.append(self.osp_dir)
    import l1b_geo_config
    if(self.run_config is not None):
      dem = ecostress.create_dem(self.run_config)
      ecostress.setup_spice(self.run_config)
    else:
      datum = os.environ['AFIDS_VDEV_DATA']+'/EGM96_20_x100.HLF'
      srtm_dir = os.environ['AFIDS_DATA']+'/srtmL2_filled'
      dem = geocal.SrtmDem(srtm_dir, False, geocal.DatumGeoid96(datum))
    cam = geocal.read_shelve(self.osp_dir + "/camera.xml")
    cam.focal_length = l1b_geo_config.camera_focal_length

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

    c2k = 273.15
    p7r = np.poly1d([PRT[0,0], -(PRT[0,1]+PRT[0,2])] )
    prc = [n for n in range(5)]
    prh = [n for n in range(5)]
    prc[0] = np.poly1d([ PRT[1,2], PRT[1,1], PRT[1,0]+c2k ]) # PRT_313_T
    prc[1] = np.poly1d([ PRT[2,2], PRT[2,1], PRT[2,0]+c2k ]) # PRT_314_T
    prc[2] = np.poly1d([ PRT[4,2], PRT[4,1], PRT[4,0]+c2k ]) # PRT_317_T
    prc[3] = np.poly1d([ PRT[3,2], PRT[3,1], PRT[3,0]+c2k ]) # PRT_315_T
    prc[4] = np.poly1d([ PRT[5,2], PRT[5,1], PRT[5,0]+c2k ]) # PRT_318_T
    prh[0] = np.poly1d([ PRT[12,2], PRT[12,1], PRT[12,0]+c2k ]) # PRT_465_T
    prh[1] = np.poly1d([ PRT[13,2], PRT[13,1], PRT[13,0]+c2k ]) # PRT_466_T
    prh[2] = np.poly1d([ PRT[14,2], PRT[14,1], PRT[14,0]+c2k ]) # PRT_467_T
    prh[3] = np.poly1d([ PRT[15,2], PRT[15,1], PRT[15,0]+c2k ]) # PRT_468_T
    prh[4] = np.poly1d([ PRT[16,2], PRT[16,1], PRT[16,0]+c2k ]) # PRT_469_T

#  Get EV start codes for BB and IMG pixels
    RPM = 0
    FP_DUR = 0
    MAX_FPIE = 0
    FPPSC = 0
    ev_codes = np.zeros( (4,6), dtype=np.int32 )
    ev_names = [ e0 for e0 in range(5) ]
    ' open EV codes file '
    with open( self.osp_dir + "/ev_codes.txt", "r") as ef:
      for i,evl in enumerate(ef):
        e0, e1, e2, e3, e4 = re.split(r'\s+', evl.strip())
        ev_names[i] = e0
        if i<4:
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
                                  ev_codes[i,0],ev_codes[i,1],
                                  ev_codes[i,2],ev_codes[i,3],
                                  ev_codes[i,4],ev_codes[i,5] ))
        else:
          RPM = float( e1 )   #RPM = 25.396627  # 25.4 nominal
          FP_DUR = float( e2 )/1000000.0   #FP_DUR = 0.000032196620  # 0.0000322 nominal
          MAX_FPIE = int( e3 )  #MAX_FPIE=1749248
          FPPSC = int( e4 )
          print("RPM=%f FP_DUR=%20.10f MAX_FPIE=%d FPPSC=%d" %( RPM, FP_DUR, MAX_FPIE, FPPSC) )

    ef.close()

    if RPM==0.0 or FP_DUR==0.0 or MAX_FPIE==0 or FPPSC==0:
      print("*** Input parameters not set ***")
      return -3
    PKT_DUR = FP_DUR * float( FPPPKT )
    PKT_DURT = PKT_DUR*.05  # PKT duration tolerance
    IMG_DUR = FP_DUR * float( FPPSC )
    PIX_DUR = FP_DUR * float( BBLEN*2 + FPPSC )
    MPER = 60.0/RPM # mirror period = 2.3622047 sec / rev
    SCAN_DUR = MPER/2.0 # half-mirror rotation = 1.1811024 sec
    FP_ANG = FP_DUR*RPM*6.0 # FP angle = .0047175926 deg / FP
    '''
    FOV = FP_DUR*RPM*6.0*FPPSC # field of view = 25.475000 deg / scan
    ANG_INC = 360.0 / float( MAX_FPIE )  # = 0.00020580272 deg/count
    ANG1 = FOV / 2.0
    ANG0 = -ANG1
    ANG2 = float( int( (ANG1 + FP_ANG*float(BBLEN*2))*1000.0 ) )/1000.0
    '''
    # FPIE mirror encoder - 50.95 degree swath width
    # covered by 25.475 degree of mirror scan.  Mirror
    # is 2-sided, so every other scan is 180 degrees apart
    EV_DUR = 60.0/RPM/float( MAX_FPIE )  # = 1.3504 microsecond/count
    FP_EV = FP_DUR*RPM*MAX_FPIE/60.0 # = 23.84375 counts/FP
    FP_EVT = FP_EV*1.1  # FP EV count tolerance
    PKT_EV = FP_DUR*RPM*MAX_FPIE*FPPPKT/60.0 # = 1525.460873 counts/PKT
    #IMG_EV = FP_DUR*RPM*MAX_FPIE*FPPSC/60.0 # = 128710.76112 counts/IMG

    det = [EV_DUR*((ev_codes[0,2]-ev_codes[2,0])%MAX_FPIE - (FPPSC-FPPPKT)*FP_EV), # btw IMG and HBB
           EV_DUR*((ev_codes[1,0]-ev_codes[0,0])%MAX_FPIE),  # btw HBB and CBB
           EV_DUR*((ev_codes[2,0]-ev_codes[1,0])%MAX_FPIE)]  # btw CBB and IMG
    print("DET: %f %f %f" %( det[0], det[1], det[2] ) )

#  get orbit number

    m=re.search('L0B_(.+?)_',self.l0b)
    if m:
      onum = m.group(1)
      print("Orbit number from file name: %s" %onum )
    else:
      print("*** Could not find orbit number from L0B file name %s" %self.l0b)
      return -1

# open L0B file
    self.fin = h5py.File(self.l0b,"r", driver='core')
    bip=self.fin["flex/bip"]
    tot_pkts = bip.shape[0]
    print("Opened L0B file %s, TOT_PKTS=%d" % (self.l0b, tot_pkts ) )

    fpie_sync = np.zeros( tot_pkts, dtype=np.int64 )
    fsw_sync = np.zeros( tot_pkts, dtype=np.int64 )
    lid=self.fin["flex/id_line"]
    pid=self.fin["flex/id_packet"]
    flex_st=self.fin["flex/state"]
    fswt=self.fin["flex/time_fsw"]
    fpie_sync[:]=self.fin["flex/time_sync_fpie"]
    fsw_sync[:]=self.fin["flex/time_sync_fsw"]
    att=self.fin["hk/bad/hr/attitude"]
    pos=self.fin["hk/bad/hr/position"]
    vel=self.fin["hk/bad/hr/velocity"]
    terr=self.fin["hk/bad/hr/time_fsw"]
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

#  Set up band order

    if bip.shape[3]==6:
      BANDS = 6
      bo = [5, 3, 2, 0, 1, 4]
      BandSpec = [1.6, 8.2, 8.7, 9.0, 10.5, 12.0]
    elif bip.shape[3] == 5:
      BANDS = 5
      bo = [3, 2, 0, 1, 4]
      BandSpec = [8.28, 8.78, 9.2, 10.49, 12.09]
    elif bip.shape[3] == 4:
      BANDS = 4
      bo = [2, 0, 1, 4]
      BandSpec = [8.78, 9.2, 10.49, 12.09]
    else:
      BANDS = 3
      bo = [1, 0, 2]
      BandSpec = [8.7, 10.5, 12.0]

    tdpuio = 0
    tcorr = 0
    iss_tcorr = 0
    if "/hk/bad/hr/time_dpuio" in self.fin and "/hk/bad/hr/time_error_correction" in self.fin:
      tdpuio = self.fin["/hk/bad/hr/time_dpuio"]
      tcorr = self.fin["/hk/bad/hr/time_error_correction"]
      if tdpuio.shape[0] > 0 and tcorr.shape[0] > 0:
        print("ISS %s time error correction %d %f" %(onum, tdpuio[0], tcorr[0]))
        iss_tcorr = tcorr.shape[0]
      else:
        print("No ISS %s time correction in file" % onum )
    else:
        print("No ISS %s time correction in file" % onum )

    epc = bb_time.shape[0]
    bbtime = np.zeros( epc, dtype=np.float64 )
    bbtime[:] = bb_time[:]
    bbfsw = np.zeros( epc, dtype=np.float64 )
    bbfsw[:] = bb_fsw[:]
    ' create engineering file and datasets '
    print("creating ENG file, EPC=%d" % epc )
    if epc > 0:
      eng, eng_met, fname = self.create_file( "L1A_ENG", int(onum), None,
            Time.time_gps(bbtime[0]), Time.time_gps(bbtime[epc-1]),
                                            primary_file=True )
    else:
      print("No HK time in L0B file")
      return -4
    eng_g = eng.create_group("/rtdBlackbodyGradients")
    rtd295 = eng_g.create_dataset("RTD_295K", shape=(epc,5), dtype='f4')
    rtd295.attrs['Units']='K'
    rtd295.attrs['valid_min']='290'
    rtd295.attrs['valid_max']='320'
    rtd295.attrs['fill']='-9999'
    rtd325 = eng_g.create_dataset("RTD_325K", shape=(epc,5), dtype='f4')
    rtd325.attrs['Units']='K'
    rtd325.attrs['valid_min']='320'
    rtd325.attrs['valid_max']='330'
    rtd325.attrs['fill']='-9999'
    rtdtime = eng_g.create_dataset("time_j2000", shape=(epc,2), dtype='f8')
    rtdtime.attrs['Units']='seconds'
    rtdtime.attrs['valid_min']='0'
    rtdtime.attrs['valid_max']='N/A'
    rtdtime.attrs['fill']='-9999'
    for i in range(epc):  # Convert DNs to Kelvin with PRT parameters
      for j in range( 5 ):
        rtd295[i,j] = prc[j]( p7r( bbt[i,0,j] ) )
        rtd325[i,j] = prh[j]( p7r( bbt[i,1,j] ) )
      rtdtime[i,0] = Time.time_gps( bbtime[i] ).j2000  # sample time
      rtdtime[i,1] = Time.time_gps( bbfsw[i] ).j2000  # hk pkt time
    rtd295.attrs['Units']='K'
    rtd295.attrs['valid_min']='290'
    rtd295.attrs['valid_max']='300'
    rtd295.attrs['fill']='N/A'
    rtd325.attrs['Units']='K'
    rtd325.attrs['valid_min']='320'
    rtd325.attrs['valid_max']='330'
    rtd325.attrs['fill']='N/A'
    eng_met.set('ImageLines', 0)
    eng_met.set('ImagePixels', 0)
    eng_met.set('SISVersion', '1')
    #eng_met.set('FieldOfViewObstruction', fov_obst) # need code arrangement
    eng_met.write()
    eng.close()

    ' create raw attitude/ephemeris file and datasets '
    aqc = att.shape[0]
    print("creating raw ATT file, AQC=%d" % aqc )
    if aqc > 0:
      attf, attf_met, attfname = self.create_file("L1A_RAW_ATT", int(onum), None,
           Time.time_gps(att_time[0]), Time.time_gps(att_time[aqc-1]),
                                        prod=False, intermediate=True)
    else:
      print("No ATT data in L0B file")
      return -5
    att_g = attf.create_group("/Attitude")
    a2k = att_g.create_dataset("time_j2000", shape=(aqc,), dtype='f8' )
    q = att_g.create_dataset("quaternion", shape=(aqc,4), dtype='f8' )
    eph_g = attf.create_group("/Ephemeris")
    e2k = eph_g.create_dataset("time_j2000", shape=(aqc,), dtype='f8' )
    epos = eph_g.create_dataset("eci_position", shape=(aqc,3), dtype='f8' )
    evel = eph_g.create_dataset("eci_velocity", shape=(aqc,3), dtype='f8' )
    for i in range(aqc):
      a2k[i] = Time.time_gps( att_time[i] ).j2000 # hk pkt time
      e2k[i] = Time.time_gps( att_time[i] ).j2000  # hk sample time
    a2k.attrs['Units']='Seconds'
    e2k.attrs['Units']='Seconds'
    q[:,:] = att[:,:]
    q.attrs['Description']='Attitude quaternion, goes from spacecraft to ECI. The coefficient convention used has the real part in the first column.'
    q.attrs['Units']='dimensionless'
    epos[:,:] = pos[:,:] * 0.3048
    epos.attrs['Description']='ECI position'
    epos.attrs['Units']='m'
    evel[:,:] = vel[:,:] * 0.3048
    evel.attrs['Description']='ECI velocity'
    evel.attrs['Units']='m/s'
    attf_met.set('ImageLines', 0)
    attf_met.set('ImagePixels', 0)
    attf_met.set('SISVersion', '1')
    #attf_met.set('FieldOfViewObstruction', fov_obst) # need code arrangement
    attf_met.write()
    attf.close()

    # correct for time code error from new firmware

    if onum >= '04227':
      print("Correcting for PKT time code error")
      fswtc_err = 1
      '''
      lids = np.zeros( (tot_pkts,FPPPKT), dtype=np.int32)
      lids[:,:] = lid[:,:]
      dev = (lids[:,FPPPKT-1] - lids[:,0]) % MAX_FPIE
      nfpies = fpie_sync[:] - 1000000*dev[:]/740500
      fpie_sync = nfpies[:]
      nfsws = fsw_sync[:]
      nfsw = fswt[:]
      for i in range(tot_pkts):
        if fpie_sync[i] < nfsws[i]:
          nfsws[i] = nfsws[i] - 1000000
          nfsw[i] = nfsw[i] - 1
      fswt = nfsw[:]
      fsw_sync = nfsws[:]
      '''
    else:
      fswtc_err = 0
    fswtc_err = 0  # Correction moved to L0B 2019-05-31

    # calculate FSW times of each packet (GPS times)

    gpt = np.zeros( tot_pkts, dtype=np.float64 )
    gpt[:] = fswt[:] + ( fpie_sync[:] - fsw_sync[:] ) / 1000000.0

    # extract encoder values
    i,j = lid.shape
    lev = np.zeros( (i,j), dtype=np.int32 )
    lev[:,:] = lid[:,:]&0x1fffff
    ldd = np.zeros( j-1, dtype=np.float32 )

    # working array
    flex_buf = np.zeros( (PPFP, FPPPKT, BANDS), dtype=np.uint16 )
    # output file arrays
    img = np.zeros( ( SCPS*PPFP, FPPSC, BANDS ), dtype=np.uint16 )
    hbb = np.zeros( ( SCPS*PPFP, BBLEN, BANDS ), dtype=np.uint16 )
    cbb = np.zeros( ( SCPS*PPFP, BBLEN, BANDS ), dtype=np.uint16 )
    pix_time = np.zeros( SCPS*PPFP, dtype=np.float64 )
    ev_buf = np.zeros( (SCPS, FPPSC), dtype=np.uint32 )
    obuf = [0,1,2]
    obuf[0] = hbb
    obuf[1] = cbb
    obuf[2] = img

    good = np.zeros( 3, dtype=np.float32 )
    gpix = np.zeros( 3, dtype=np.float32 )
    scenes = []  # record refined scene start/stop times

    pkt_idx = 0 # start looking at first packet in file
    # iterate through scenes from scene start/stop file
    o_start_time = None
    jumps = 0
    remain = -1234
    sst0 = 0
    for orbit, scene_id, sts, ste in self.process_scene_file():
      orb = str( "%05d" %orbit )
      if orb != onum:  # process only matching orbit numbers
        print("Ignoring mismatch orbit number %s, ref=%s scene=%d" %(orb, onum, scene_id) )
        continue
      print("====  ", datetime.now(), "  ====")
      dt = ste.gps - sts.gps
      print("SCENE=%03d START=%s(%f) END=%s(%f) DT=%f" % ( scene_id, sts, sts.gps, ste, ste.gps, dt) )

      # detect field of view obstruction
      fov_obst = self.detect_obst( sts, ste )

      good[:] = 0.0

      #*** Assume packets in time sequence ***
      ' search for packet containing scene start time '
      if sts.gps > gpt[tot_pkts-1]:
        t0 = Time.time_gps( gpt[tot_pkts-1] )
        print("Scene time %s(%f) past data time %s(%f)" %( sts, sts.gps, t0, gpt[tot_pkts-1] ) )
        continue  # go to next scene
      pkt_idx = np.argmax( gpt>sts.gps )
      if pkt_idx > 0: pkt_idx -= 1
      t0 = Time.time_gps( gpt[pkt_idx] )
      dt = t0 - sts
      print("Located scene %s start time %f in PKT[%d] %s(%f) DT=%f" % ( scene_id, sts.gps, pkt_idx, str(t0), t0.gps, dt ) )
      rst = t0.gps - dt
      rse = ste.gps  # initialize refined scene end time
      print("Initial guess of refined scene start/end time %s(%f) %s(%f)" %( Time.time_gps(rst), rst, Time.time_gps(rse), rse) )

      # initialize buffers to fill values
      img[ :,:,: ] = 0xffff
      hbb[ :,:,: ] = 0xffff
      cbb[ :,:,: ] = 0xffff
      pix_time[ : ] = 0.0
      ev_buf[ :,: ] = 0xffffffff

      line = 0  # line pointer in output image
      pxet = t0 + PIX_DUR  # BB and IMG pixel end time

      scan = 0
      scans = 0
      if pkt_idx > 0: pkt_idx -= 1 # compensate for time code error

      while scan < SCPS and pxet < ste:

        cont = 1
        flex_buf[:,:,:] = 0xffff
        e1 = 0
        #  Loop through HBB, CBB, and IMG sequences in scan
        seq = 0
        gpix[:] = 0
        ph0 = 2
        ph0_idx = 0
        while seq<3:
          e0 = pkt_idx
          ph = 2  # mirror phase should be 0 or 1
          while e0 < tot_pkts and ph == 2:  # search for sequence start
            if e0==0: dt = 0
            else: dt = ( float((lev[e0,0] - lev[e0-1,e1])%MAX_FPIE) ) * EV_DUR
            adt = abs( dt )
            if gpt[e0] > rse:  # packet time past end of scene
              scans = scan
              sse = rst + scans * SCAN_DUR
              print("** Finish orbit %05d short scene %s SCANS=%d end=%s(%f) GPT=%s(%f) at %d" % (orbit, scene_id, scans, Time.time_gps(sse), sse, Time.time_gps(gpt[e0]),gpt[e0],e0 ) )
              scan = SCPS  # force finish up current scene
              seq = 3
              cont = 0
              pxet = ste  # force out of scan loop
              break

            if adt > SCAN_DUR and seq > 0:
              print("** Discontinuity seeking %s IDX=%d DT=%f E1=%d" %(ev_names[seq],e0,dt,e1))
              cont = 0

              scan = int( (gpt[e0] - rst) / SCAN_DUR )
              print("** start Next scan %d" % scan )

              seq = 3  # force exit SEQ loop
              break # break out of packets loop

            # find start of sequence and mirror phase in PKT
            e1 = 0
            while e1 < FPPPKT and ph == 2:
              lid0 = ( lev[e0,e1] + ev_codes[seq,4] ) % MAX_FPIE
              lid1 = ( lev[e0,e1] + ev_codes[seq,5] ) % MAX_FPIE
              if lid0 >= ev_codes[seq,0] and lid0 <= ev_codes[seq,1]: ph = 0
              elif lid1 >= ev_codes[seq,2] and lid1 <= ev_codes[seq,3]: ph = 1
              else: e1 += 1 # check next EV
            ' end seeking SEQ in current packet '

            if ph == 2:
              e0 += 1 # look in next packet
              e1 = 0
          ' End seeking SEQ through packets '
          print("Out of SEQ seek E0=%d E1=%d" %(e0,e1))

          if e0>=tot_pkts: # hit EOF; finish up any existing scans
            print("** Hit EOF ")
            e0 = tot_pkts - 1
            e1 = FPPPKT - 1
            cont = 0
            scans = scan  # save any scans already copied
            scan = SCPS  # force out of scan loop

          pkt_idx = e0
          if cont==0:  break # discont in SEQ seek, break out of SEQ loop

        # check phase
          '''
          if seq==0:  # record reference mirror phase
            ph0 = ph
            ph0_idx = e0
          else:
            if ph != ph0:
              print("Phase mismatch EXP=%d[%d] ACT=%d PKT=%d" %(ph0, ph0_idx, ph, e0))
              e0 = ph0_idx+1  # backup to packet after PH0
              seq = 0
              continue  # skip remaining SEQ processing and restart
          '''

        # Found start of SEQ, check continuity of first SEQ PKT

          if e0<tot_pkts-1: lid1 = e0+1
          else: lid1 = e0
          lid0 = lid1 - 1
          if lid0<0: lid0=0
            
          l0 = lev[lid0,e1] - int( FP_EV+0.5 )  #  add 1 FP of counts
          if e1==0:  #  ends in current packet
            dt = (float((lev[lid0,FPPPKT-1] - l0)%MAX_FPIE)) * EV_DUR
          else:  #  ends in next packet
            dt = (float((lev[lid1,e1-1] - l0)%MAX_FPIE)) * EV_DUR
          adt = abs( dt-PKT_DUR )
          if adt > PKT_DURT or e0>=tot_pkts-1:
            print("Scene %d Disco %s, terminating scan %d E0=%d E1=%d DT=%f" %(scene_id,ev_names[seq],scan,e0,e1,dt))
            pkt_idx = e0+1  # get past current packet
            scan += 1
            cont = 0
            seq = 3  # break out of sequence loop to next scan
            op = 0
            break

          # calculate fswt of first FP in SEQ
          if fswtc_err == 1:  # use time from previous PKT+FP_DUR
            dpt = e0 - 1
            if dpt<0: dpt = 0
            fswtc = FP_DUR
          else:
            dpt = e0;fswtc = 0.0
          if e1==0:  #  Seq starts at beginning of PKT
            p0t = gpt[e0] - fswtc * FPPPKT
          else:  #  count backward from next PKT
            dt = (FPPPKT-e1) * FP_DUR
            p0t = gpt[dpt+1] - dt + fswtc
          dpt = gpt[lid1] - gpt[lid0]

          # calculate ISS time correction
          if iss_tcorr>0:
            tdx = np.argmax( p0t < terr )
            if tcorr[tdx] >= 2147483648: tc = (tcorr[tdx]-4294967296)
            else: tc = tcorr[tdx]
            print("Scene %d scan %d TCORR=%f TDX=%d" %(scene_id, scan, tcorr[tdx], tdx) )
          else: tc = 0.0
          if seq==0:  # save scan start time
            sst = p0t
            scan = int( ( sst - rst ) / SCAN_DUR + 0.5 )
            dst = sst - sst0
            std = dst - SCAN_DUR
            fpd = std / FP_DUR
            sst0 = sst
            print("Calculated scan=%02d SCENE=%s SST=%f RST=%f DST=%f STD=%9f FPD=%9f" % (scan, scene_id, sst, rst, dst, std, fpd ))
            if scan >= SCPS:
              print("PKT[%d] Time %f outside of current scene %d Terminating" %( e0, gpt[e0], scene_id ) )
              cont = 0
              break
            line = scan * PPFP

          elif seq==2:  # save and replicate IMG start time
            if scan==0:  # save refined scene start time of IMG
              rst = p0t
              #tc0 = tc
            print("Orbit %s SCENE %d SCAN %d P0T=%f" %(orb,scene_id,scan,p0t))
            #pix_time[line:line+PPFP] = Time.time_gps( p0t-tc ).j2000
            pix_time[line:line+PPFP] = Time.time_gps( p0t ).j2000

          print("Found %s LID[%d,%d]=%d PH=%d SCENE=%s SCAN=%d GPS=%f DPT=%f %s"%(ev_names[seq],e0,e1,lev[e0,e1],ph,scene_id,scan,p0t,dpt,Time.time_gps(p0t)))
  
          # Copy pixels from PKT
          p1 = e1
          fpc = FPPPKT - p1  # FPs to copy from first PKT

          op0 = ev_codes[3,seq]  # starting output fp of sequence
          op1 = ev_codes[3,seq+1]  # ending output fp of sequence
          op = op0  # initialize output FP pointer

          while op < op1 and e0 < tot_pkts:
            #print("SCENE=%d SCAN=%d E0=%d E1=%d GPS=%f SEQ=%d OP=%d" %(scene_id,scan,e0,e1,gpt[e0], seq, op))

            remain = op1 - op  # remaining FPs to fill in current scan
            opinc = 0
            #  calculate delta time between packets
            if e0 == tot_pkts-1:  # at last packet in file
              dt = PKT_DUR
              lid0 = e0-1; lid1 = e0
            else:
              if fswtc_err == 1:lid0 = e0-1; lid1 = e0  # time code error
              else: lid0 = e0; lid1 = e0+1  # correct time
              dt = gpt[lid1] - gpt[lid0]
            #if p1==0: sq = (seq-1)%3
            #else: sq = seq

            '''  check against expected delta T between sequences  '''
            if op>op0 and (dt<0 or abs(dt-PKT_DUR)>PKT_DURT) and seq==2:  # time discontinuity

              ldd[:] = (lev[e0,1:] - lev[e0,:FPPPKT-1])%MAX_FPIE  # find FP with EV jump
              fpc = np.argmax( ldd > FP_EVT )
              if fpc==0:
                if ldd[0]>FP_EVT: fpc = 1
                else: fpc = FPPPKT
              else: fpc += 1

              if fpc < remain:  # jump occurred before end of IMG

                jumps += 1
                print("*** Orbit %s Scene %d scan %d %s Time jump PKT=%d %s DT=%10.8f OP=%d " %(orb, scene_id, scan, ev_names[seq], lid1,Time.time_gps(gpt[lid1]),dt,op), end="")

                if dt > IMG_DUR - (op1-op)*FP_DUR:  # jump outside of current IMG, go to next scan
                  print("past IMG seq", end="")
                # elif dt > det[sq] or dt<0:  # greater than normal time gap or negative

                if e0==tot_pkts - 1:  # at end of data
                  dev = 0.0
                  d2 = 0.0
                else:  # check EV continuity to next packet
                  dev = abs( (lev[lid1,0] - lev[lid0,0]) - FP_EV * FPPPKT )
                  d2 = abs( (lev[lid1,FPPPKT-1] - lev[lid0,FPPPKT-1]) - FP_EV * FPPPKT )
                if (op==op0 and d2<=FP_EVT) or (op>=op1-FPPPKT and dev<=FP_EVT) or (dev<=FP_EVT and d2<=FP_EVT): opinc=0 # EV continuous
                else: opinc = int( dt/FP_DUR + 0.5 ) - FPPPKT

                if dt<0: print("Negative time jump", end="")
                else: print(" ...continuing", end="")

                print(" OPINC=%d  ***" %opinc)
                print("Copying remaining %d FPs from PKT [%d,%d] to scan %d at %d" % (fpc, e0, p1, scan, op))
              # End jump detection

            for b in range( BANDS ): # transpose new packet to flex_buf
              flex_buf[:,:,b] = np.transpose(bip[e0,:,:,b])

            if fpc >= remain:
              fpc = remain  # runt at end of sequence
              print("Last %s chunk:%d FPC=%d IDX=[%d,%d] OP=%d" %(ev_names[seq],remain,fpc,e0,p1,op), end="")
              if seq==2:
                sse = gpt[e0-1] + PKT_DUR + fpc*FP_DUR + FP_DUR
                print(" SSE=%f" % sse )
              else:
                print(" NULL")
              if remain==FPPPKT: remain = 0  # next search in next packet

            dp = op - op0
            #print("SEQ=%d LINE=%d OP=%d DP=%d P1=%d FPC=%d E0=%d REMAIN=%d OPINC=%d" %(seq,line,op,dp,p1,fpc,e0,remain,opinc))
            obuf[seq][line:line+PPFP,dp:dp+fpc,:] = flex_buf[:,p1:p1+fpc,:]
            if seq==2: ev_buf[scan,dp:dp+fpc] = lev[e0,p1:p1+fpc]
            gpix[seq] += fpc

            if (e0<tot_pkts-1) and pid[lid1]>1 and (int(pid[lid1]) - int(pid[lid0]))!=1:  # skip non-consecutive packet ID
              print("found non-contiguous PKT %d PIDs=%d %d" % ( lid1, pid[lid0], pid[lid1] ) )

              if opinc<0:
                e0 +=1
                print("Skipping disco PKT %d ID=%d" %( e0, pid[e0] ) )
                opinc = 0

            op = op + opinc + fpc
            if op<op0 or op>op1:  # next packet outside of current scan
               cont = 1
               sse = gpt[e0-1] + PKT_DUR + fpc * FP_DUR + FP_DUR
               print("Terminating scan %d in %s at FP %d E0=%d SSE=%f" % (scan,ev_names[seq],op,e0,sse))
               seq = 3  # force exit SEQ loop
               op = 0
               break
            fpc = FPPPKT # full PKTs after (partial) first PKT
            p1 = 0
            e0 += 1

          # end seq copy loop
          if e0>=tot_pkts:
            sse = gpt[pkt_idx] + PKT_DUR + FP_DUR
            pkt_idx = tot_pkts - 1
          else:
            if op>op0 and remain>0: pkt_idx = e0-1
            else: pkt_idx = e0
          if cont==0: break  # drop into scan loop
          seq += 1
        # end seq loop

        print("SCENE=%s SCAN=%d SCANS=%d LINE=%d DT=%f s2k=%f IDX=%d REMAIN=%d OP=%d RSE=%f"%(scene_id,scan,scans,line,dt,pix_time[scans],pkt_idx,remain,op,rse))

# cont==0 from:
# - No SEQ from scene start time
#   restart scan loop with scan=0, scans=0, new IDX and scene start time

        if cont==0:
          if scans==0:  # restart scanning with new IDX
            scan = 0
          if pkt_idx==tot_pkts-1:  # EOF
             break  # break out of scan loop
        else:
          good[:] += gpix[:]
          pxet += SCAN_DUR
          scans += 1
          scan += 1

      # end scan loop
      print("Out of scan loop scan=%d scans=%s" %( scan, scans ))

      if scans==0: continue  # skip rest of processing

      good_bb = good[0] + good[1]
      bb_cnt = scans*2*BBLEN
      good_img = good[2]
      img_cnt = scans*FPPSC
      #rse = sse - tc  # refined scene end time
      rse = sse  # refined scene end time
      #if o_start_time is None: o_start_time = Time.time_gps( rst-tc0 )
      if o_start_time is None: o_start_time = Time.time_gps( rst )
      o_end_time = Time.time_gps( rse )
      scenes.append("%05d	%03d	%s	%s\n" %( orbit, scene_id,
        str( Time.time_gps( rst ) )[:26], str( Time.time_gps( rse ) )[:26] ) )
        #str( Time.time_gps( rst-tc0 ) )[:26], str( Time.time_gps( rse ) )[:26] ) )

      # copy to output files

      ''' ***  Use input BBbb and VV in file name  *** '''

      ' create scene file and image pixel, J2K, and FPIE EV groups '
      l1a_fp, l1a_fp_met, pname = self.create_file( "L1A_RAW_PIX", orbit, scene_id,
         Time.time_gps(rst), Time.time_gps(rse), prod=False, intermediate=True)
         #Time.time_gps(rst-tc0), Time.time_gps(rse), prod=False, intermediate=True)

      ' create BB file and BlackBodyPixels group '
      l1a_bp, l1a_bp_met, fname = self.create_file( "L1A_BB", orbit, scene_id,
              Time.time_gps(rst), Time.time_gps(rse), prod=True )
              #Time.time_gps(rst-tc0), Time.time_gps(rse), prod=True )

      ' record scan completeness '
      pcomp = float( good_img ) / float( img_cnt )
      #l1a_fp_met.set('AutomaticQualityFlag', '%16.10e' % pcomp)
      if pcomp > .95:
        l1a_fp_met.set('AutomaticQualityFlag', '%s' % 'PASS')
      else:
        l1a_fp_met.set('AutomaticQualityFlag', '%s' % 'FAIL')
      bcomp = float( good_bb ) / float( bb_cnt )
      #l1a_bp_met.set('AutomaticQualityFlag', '%16.10e' % bcomp)
      if bcomp > .95:
        l1a_bp_met.set('AutomaticQualityFlag', '%s' % 'PASS')
      else:
        l1a_bp_met.set('AutomaticQualityFlag', '%s' % 'FAIL')

      sst = str( datetime.now() )[0:19]
      print("====  %s  ===" %sst )
      print("Orbit %s SCENE %s completed, SCANS=%d (%f) %d/%d GOOD/IMG, (%f) %d/%d GOOD/BB" % ( orb, scene_id, scans, pcomp, good_img, img_cnt, bcomp, good_bb, bb_cnt ))

      e0, e1, e2 = img.shape
      print("Writing file %s size=%d %d %d BANDS=%d" %( pname, e0, e1, e2, BANDS ) )
      l1a_fp_met.set('ImageLines', img.shape[0])
      l1a_fp_met.set('ImageLineSpacing', '34.377')
      l1a_fp_met.set('ImagePixels', img.shape[1])
      l1a_fp_met.set('ProductionLocation', 'ECOSTRESS Science Data System')
      l1a_fp_met.set('PlatformLongName', 'International Space Station')
      l1a_fp_met.set('ProcessingLevelDescription', 'L1A Raw Pixels')
      #l1a_fp_met.set('ProductionDateTime', sst ) # given in runconfig file
      l1a_fp_met.set('ShortName', 'L1A_RAW')
      l1a_fp_met.set('SISVersion', '1')
      l1a_fp_met.set('FieldOfViewObstruction', fov_obst)
      l1a_fp_met.write()

      l1a_bp_met.set('ImageLines', cbb.shape[0])
      l1a_bp_met.set('ImageLineSpacing', '0')
      l1a_bp_met.set('ImagePixels', cbb.shape[1])
      l1a_bp_met.set('ImagePixelSpacing', '0')
      l1a_bp_met.set('ProductionLocation', 'ECOSTRESS Science Data System')
      l1a_bp_met.set('PlatformLongName', 'International Space Station')
      l1a_bp_met.set('ProcessingLevelDescription', 'L1A Black Body')
      #l1a_bp_met.set('ProductionDateTime', sst ) # given in runconfig file
      l1a_bp_met.set('ShortName', 'L1A_BB')
      l1a_bp_met.set('SISVersion', '1')
      l1a_bp_met.set('FieldOfViewObstruction', fov_obst)
      l1a_bp_met.write()

# L1A_RAW_PIX metadata

      pcomp = 100.0 * ( 1.0 - float( good_img ) / float( FPPSC * SCPS ) )
      print("Percent missing data=%f" %pcomp )
      l1a_metag = l1a_fp['/L1A_RAW_PIXMetadata']
      l1a_qamissing = l1a_metag.create_dataset('QAPercentMissingData', data=pcomp, dtype='f4' )
      l1a_qamissing.attrs['Units']="percentage"
      l1a_qamissing.attrs['valid_min'] = 0
      l1a_qamissing.attrs['valid_max'] = 100

      if iss_tcorr>0:  #  record ISS time error correction into L1A_RAW file
        e0 = np.argmax( rst<terr )
        e1 = np.argmax( rse<terr )
        if e1 - e0 > 0:
          l1a_te=l1a_metag.create_dataset('ISS_time', data=terr[e0:e1], dtype='f8')
          l1a_td=l1a_metag.create_dataset('ISS_time_dpuio', data=tdpuio[e0:e1], dtype='i8')
          l1a_tc=l1a_metag.create_dataset('ISS_time_error_correction', data=tcorr[e0:e1], dtype='f8')

# Other L1A_RAW and BB data componente

      l1a_ptg = l1a_fp.create_group("/Time")
      t = l1a_ptg.create_dataset("line_start_time_j2000", data=pix_time,
                                 dtype="f8" )
      t.attrs["Description"] = "J2000 time of first pixel in line"
      t.attrs["Units"] = "second"

      l1a_peg = l1a_fp.create_group("/FPIEencoder")
      t = l1a_peg.create_dataset("EncoderValue", data=ev_buf, dtype="u4" )
      t.attrs["Description"] = "FPIE mirror pistion encoder values of each FP"
      t.attrs["Units"] = "dimensionless"
      t.attrs['valid_min']='0'
      t.attrs['valid_max']='1749247'
      t.attrs['fill']='0xffffffff'

      l1a_upg = l1a_fp.create_group("/UncalibratedPixels")
      l1a_bpg = l1a_bp.create_group("/BlackBodyPixels")
      l1a_rtg = l1a_bp.create_group("/rtdBlackbodyGradients")
      for b in range( BANDS ):
        t = l1a_upg.create_dataset("pixel_data_%d" %(b+1),
                                   data=img[:,:,bo[b]],
                                   chunks=(PPFP,FPPSC), dtype="u2" )
#  not compressing a non-delivered product to save a little time
        t.attrs['Units']='dimensionless'
        t.attrs['valid_min']='0'
        t.attrs['valid_max']='32767'
        t.attrs['fill']='0xffff'

        #if BANDS==6:
        e0 = np.argmax( img[:,:,bo[b]] != 0xffff )
        if e0==0 and img[0,0,bo[b]]==0xffff: BandSpec[b] = 0.0

        t = l1a_bpg.create_dataset("b%d_blackbody_295" %(b+1),
                                   data=cbb[:,:,bo[b]], chunks=(PPFP,BBLEN),
                                                  dtype="u2", compression="gzip" )
        t.attrs['Units']='dimensionless'
        t.attrs['valid_min']='0'
        t.attrs['valid_max']='32767'
        t.attrs['fill']='0xffff'
        t = l1a_bpg.create_dataset("b%d_blackbody_325" %(b+1),
                                   data=hbb[:,:,bo[b]], chunks=(PPFP,BBLEN),
                                                  dtype="u2", compression="gzip" )
        t.attrs['Units']='dimensionless'
        t.attrs['valid_min']='0'
        t.attrs['valid_max']='32767'
        t.attrs['fill']='0xffff'

      l1a_BandSpec = l1a_metag.create_dataset('BandSpecification', data=BandSpec, dtype='f4' )
      l1a_BandSpec.attrs["Units"] = "micrometer"
      l1a_BandSpec.attrs["valid_min"] = 1.6
      l1a_BandSpec.attrs["valid_max"] = 12.1
      l1a_BandSpec.attrs["fill"] = 0

# L1A_BB metadata

      bcomp = 100.0 * ( 1.0 - float( good_bb ) / float( BBLEN*2*SCPS ) )
      l1a_metag = l1a_bp['/L1A_BBMetadata']
      l1a_qamissing = l1a_metag.create_dataset('QAPercentMissingData', data=bcomp, dtype='f4' )
      l1a_qamissing.attrs['Units']="percentage"
      l1a_qamissing.attrs['valid_min'] = 0
      l1a_qamissing.attrs['valid_max'] = 100
      l1a_BandSpec = l1a_metag.create_dataset('BandSpecification', data=BandSpec, dtype='f4' )
      l1a_BandSpec.attrs["Units"] = "micrometer"
      l1a_BandSpec.attrs["valid_min"] = 1.6
      l1a_BandSpec.attrs["valid_max"] = 12.1
      l1a_BandSpec.attrs["fill"] = 0

      # copy RTD temps to BB file
      if epc > 0:
        p0 = np.argmax( bbtime >= rst )
        p1 = np.argmax( bbtime >= rse )
      else:
        p0 = 0
        p1 = -1
      if p1 <= p0:
        p0 = 0
        p1 = epc - 1
      print("Copying RTD for SCENE %d P0=%d P1=%d RST=%f RSE=%f %s" %(scene_id, p0, p1, rst, rse, str(datetime.now())))
      print(" ")
      bt=l1a_rtg.create_dataset("time_j2000", shape=(p1-p0+1,), dtype='f8')
      bt.attrs['Units']='seconds'
      bt.attrs['valid_min']='0'
      bt.attrs['valid_max']='N/A'
      bt.attrs['fill']='-9999'
      r2=l1a_rtg.create_dataset("RTD_295K", shape=(p1-p0+1,5,), dtype='f4')
      r2.attrs['Units']='K'
      r2.attrs['valid_min']='290'
      r2.attrs['valid_max']='320'
      r2.attrs['fill']='-9999'
      r3=l1a_rtg.create_dataset("RTD_325K", shape=(p1-p0+1,5,), dtype='f4')
      r3.attrs['Units']='K'
      r3.attrs['valid_min']='320'
      r3.attrs['valid_max']='330'
      r3.attrs['fill']='-9999'
      for i in range( p0, p1+1 ):
        bt[i-p0] = Time.time_gps( bbtime[i] ).j2000
        for j in range( 5 ):
          r2[i-p0,j] = prc[j]( p7r( bbt[i,0,j] ) )
          r3[i-p0,j] = prh[j]( p7r( bbt[i,1,j] ) )

#  Check FOV obstruction

      l1a_fp.close()
      l1a_bp.close()

      if pcomp < 50.0:
#  Generate corner locations
        print("Getting time table")
        tt = ecostress.create_time_table(pname,
                                 l1b_geo_config.mirror_rpm,
                                 l1b_geo_config.frame_time)
        print("getting SM")
        sm = ecostress.create_scan_mirror(pname,
                                  l1b_geo_config.max_encoder_value,
                                  l1b_geo_config.first_encoder_value_0,
                                  l1b_geo_config.second_encoder_value_0,
                                  l1b_geo_config.instrument_to_sc_euler,
                                  l1b_geo_config.first_angle_per_encoder_value,
                                  l1b_geo_config.second_angle_per_encoder_value)
        print("Getting orbitt")
        orbitt = ecostress.EcostressOrbit(attfname, l1b_geo_config.x_offset_iss,
                               l1b_geo_config.extrapolation_pad,
                               l1b_geo_config.large_gap)
        print("Getting igc")
        igc = ecostress.EcostressImageGroundConnection(orbitt, tt, cam, sm, dem, None)
        print("Getting mi")
        mi = geocal.cib01_mapinfo()
        print("Getting mi_fp")
        try:
          mi_fp = igc.cover(mi)
          if abs( mi_fp.ulc_x - mi_fp.lrc_x ) < 10.0:
            l1a_fp=h5py.File( pname, 'a')
            l1a_fp['/StandardMetadata/EastBoundingCoordinate'][()] = mi_fp.lrc_x
            l1a_fp['/StandardMetadata/SouthBoundingCoordinate'][()] = mi_fp.lrc_y
            l1a_fp['/StandardMetadata/NorthBoundingCoordinate'][()] = mi_fp.ulc_y
            l1a_fp['/StandardMetadata/WestBoundingCoordinate'][()] = mi_fp.ulc_x
            l1a_fp.close()
            print("Scene %d footprint E=%f S=%f N=%f W=%f" %(scene_id, mi_fp.lrc_x, mi_fp.lrc_y, mi_fp.ulc_y, mi_fp.ulc_x ))
          else:
            print("Scene %d footprint too big E=%f S=%f N=%f W=%f" %(scene_id, mi_fp.lrc_x, mi_fp.lrc_y, mi_fp.ulc_y, mi_fp.ulc_x ))
        except:
          print("Exception from igc.cover, no footprint for scene %d" % scene_id )
      else:
        print("Scene %s missing too many pixels (%f), not generating footprint" %(scene_id,pcomp))

    ' end scene loop '

    if len(scenes)==0:
      print("****  FATAL  ****  No scenes generated  ****")
      return -2

    sss = str( o_start_time )
    ses = str( o_end_time )
    sst = str( datetime.now() )[0:19]
    print("Create refined scene file %d %s %s %s" %( len(scenes), sss, ses, sst ) )
    sf = "Scene_%05d_%s_%s_%s.txt" % ( orbit, sss[0:4]+sss[5:7]+sss[8:13]+sss[14:16]+sss[17:19], ses[0:4]+ses[5:7]+ses[8:13]+ses[14:16]+ses[17:19], sst[0:4]+sst[5:7]+sst[8:10]+'T'+sst[11:13]+sst[14:16]+sst[17:19])
    sfd = open( sf, "w" )
    for i in range( len(scenes) ): sfd.write( scenes[i] )
    sfd.close()

    # Write out a dummy log file
    #print("This is a dummy log file", file = self.log)
    #self.log.flush()
    print("====  End Orbit %s" %orb, datetime.now(), "jumps=%d  ====" %jumps )
    return jumps
