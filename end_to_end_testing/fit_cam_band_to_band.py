# The model that Bill gave for the camera doesn't do a great job with band to band.
# Isn't exactly clear what the issue is, we tried tracking this down but it wasn't
# really clear what the underlying reason is. Probably the specific pixels choosen
# for readout didn't match what was in the spreadsheet, but that is just a guess.
#
# Instead, we can empirically adjust the principal point to improve the band to
# band registration.
#
# We collect tiepoints in the original L1A space, so before doing the 2x2 averaging and
# before applying the band to band correction.
#
# Tiepoints were collected using the collect tp function

from geocal import *
from ecostress import *
import pandas as pd
from pathlib import Path
import sys

# Can do this more complicated, but for now just have the various inputs hardcoded.
l1_osp_dir="/home/smyth/Local/ecostress-test-data/latest/l1_osp_dir"
l1a_pix = "ECOv002_L1A_PIX_35449_005_20241006T165158_0713_02.h5"
l1a_gain = "L1A_RAD_GAIN_35449_005_20241006T165158_0713_02.h5"
l1b_fname = "orb35449_l1b/ECOv002_L1B_RAD_35449_005_20241006T165158_0700_01.h5"
corr_att_fname = "ECOv002_L1B_ATT_35449_20241006T164126_0713_02.h5"
att_fname = "L1A_RAW_ATT_35449_20241006T164120_0713_01.h5"
orbit_num = 353449

sys.path.append(l1_osp_dir)
import l1b_rad_config
import l1b_geo_config

# We hold this band fixed, and do everything relative to this
ref_band = 2
# Create to igcol for all the bands
orb = ecostress.EcostressOrbit(
            att_fname, l1b_geo_config.x_offset_iss,
            l1b_geo_config.extrapolation_pad,
            l1b_geo_config.large_gap)
dem = SrtmDem()
cam = read_shelve("camera_20180208.xml")
cam.focal_length = l1b_geo_config.camera_focal_length
tt = create_time_table(l1a_pix, l1b_geo_config.mirror_rpm,
                                 l1b_geo_config.frame_time)
sm = create_scan_mirror(l1a_pix, l1b_geo_config.max_encoder_value,
                                  l1b_geo_config.first_encoder_value_0,
                                  l1b_geo_config.second_encoder_value_0,
                                  l1b_geo_config.instrument_to_sc_euler,
                                  l1b_geo_config.first_angle_per_encoder_value,
                                  l1b_geo_config.second_angle_per_encoder_value)
igccol = EcostressIgcCollection()
for band in range(1,6):
    rad = MemoryRasterImage(ScaleImage(EcostressRadApply(l1a_pix, l1a_gain, band), 100.0))
    igc = EcostressImageGroundConnection(orb, tt, cam, sm, dem, rad, f"Band {band}",
                                         30,band)
    igccol.add_igc(igc)

# Assume if tpcol already exists, we just use it. You can delete the file to
# force recreation

tpfname = f"tpcol_{orbit_num}.xml"
if not Path(tpfname).exists() :
    im = CcorrLsmMatcher()
    itoim = []
    bdata = [1,3,4,5]
    for b in bdata:
        itoim.append(IgcImageToImageMatch(igccol.image_ground_connection(ref_band-1),
                                          igccol.image_ground_connection(b-1),
                                          im))
    tpcol = []
    for scanline in range(20,256-20+10,10):
        for ln in range(0, igc.number_line, 256):
            for smp in range(0, igc.number_sample, 100):
                tp = TiePoint(5)
                tp.is_gcp = False
                ic = ImageCoordinate(ln+scanline,smp)
                tp.image_coordinate(ref_band-1,ic)
                gp = igccol.ground_coordinate(ref_band-1,ic)
                if(gp is not None):
                    tp.ground_location = gp
                    for i,b in enumerate(bdata):
                        igc1 = itoim[i].image_ground_connection1
                        igc2 = itoim[i].image_ground_connection2
                        ic2guess,success = igc2.image_coordinate_scan_index(
                            gp, ln//256)
                        if(success):
                            ic2, _, _, success, _ = itoim[i].matcher.match_mask(
                                igc1.image, igc1.image_mask,
                                igc2.image, igc.image_mask,
                                ic, ic2guess)
                        if(success):
                            tp.image_coordinate(b-1,ic2)
                    if(tp.number_image_location > 1):
                        tpcol.append(tp)
    tpcol = TiePointCollection(tpcol)
    write_shelve(f"tpcol_{orbit_num}.xml", tpcol)

tpcol = read_shelve(f"tpcol_{orbit_num}.xml")

# The different bands are completely independent, so to speed up the processing
# we just fit one at a time
band_processing = 1
fit_ref_also = False
fit_all = False
band_list = [1,3,4,5]
def residual(band=None):
    res = []
    b = band_processing if band is None else band
    igc = igccol.image_ground_connection(b-1)
    igcref = igccol.image_ground_connection(ref_band-1)
    for tp in tpcol:
        scan_index = int(tp.image_coordinate(ref_band-1).line // 256)
        iloc = tp.image_coordinate(b-1)
        if(iloc is not None):
            if(fit_ref_also):
                gp = igcref.ground_coordinate(tp.image_coordinate(ref_band-1))
            else:
                gp = tp.ground_location
            try:
                icpred, success = igc.image_coordinate_scan_index(gp,scan_index)
                if(success):
                    res.append(iloc.line - icpred.line)
                    res.append(iloc.sample - icpred.sample)
            except RuntimeError as e:
                if(str(e) != "ImageGroundConnectionFailed"):
                    raise e
    return np.array(res)

def get_igc_fit_parameters():
    res = []
    if fit_all:
        for b in band_list:
            t = cam.principal_point(b)
            res.append(t.line)
            res.append(t.sample)
    else :
        t = cam.principal_point(band_processing)
        res.append(t.line)
        res.append(t.sample)
    if(fit_ref_also):
        t = cam.principal_point(ref_band)
        res.append(t.sample)
    return np.array(res)

def set_igc_fit_parameters(val):
    if fit_all:
        i = 0
        for b in band_list:
            t = cam.principal_point(b, FrameCoordinate(val[i], val[i+1]))
            i += 2
    else:
        cam.principal_point(band_processing,FrameCoordinate(val[0], val[1]))
    if(fit_ref_also):
        cam.principal_point(ref_band,FrameCoordinate(128.0, val[-1]))
        

def res_func(v):
    print(f"res_func called with {v}")
    set_igc_fit_parameters(v)
    if fit_all:
        res = []
        for b in band_list:
            res.append(residual(band=b))
        return np.concatenate(res)
    else:
        return residual()

fit_ref_also = True
#for b in [1,3,4,5]:
for b in ():
    print(f"Working on band {b}")
    band_processing = b
    xstart = get_igc_fit_parameters()
    if fit_ref_also:
        diff_step = [0.001, 0.001, 0.001]
        # Start at the same point for each step
        xstart[2] = 16.0
    else:
        diff_step = [0.001, 0.001]
    res = scipy.optimize.least_squares(res_func, xstart, diff_step=diff_step)
    print(res)
    resresidual = residual()
    lres = pd.DataFrame(resresidual[0::2])
    sres = pd.DataFrame(resresidual[1::2])
    print(lres.describe())
    print(sres.describe())

    
# Fit everything in one step, just to see if we should move the
# sample number of our reference band
fit_all = True
xstart = get_igc_fit_parameters()

# Temp, jump to solution    
diff_step = [0.001,] * len(xstart)
res = scipy.optimize.least_squares(res_func, xstart, diff_step=diff_step)
write_shelve("camera_20250619.xml", cam)

