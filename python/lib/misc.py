# This is various miscellaneous routines that don't fit elsewhere
import geocal
import re
import subprocess
import h5py
import os
import sys
import math
import numpy as np
from ecostress_swig import *

def create_dem(config):
    '''Create the SRTM DEM based on the configuration. In production, we
    take the datum and srtm_dir passed in. But for testing if the special
    variable ECOSTRESS_USE_AFIDS_ENV is defined then we use the value 
    passed in from the environment.'''
    datum = os.path.abspath(config["StaticAncillaryFileGroup", "Datum"])
    srtm_dir = os.path.abspath(config["StaticAncillaryFileGroup", "SRTMDir"])
    if("ECOSTRESS_USE_AFIDS_ENV" in os.environ):
        datum = os.environ["AFIDS_VDEV_DATA"] + "/EGM96_20_x100.HLF"
        srtm_dir = os.environ["ELEV_ROOT"]
    dem = geocal.SrtmDem(srtm_dir,False, geocal.DatumGeoid96(datum))
    return dem

def ortho_base_directory(config):
    '''Create the ortho base. In production, take the directory passed in
    from the configuration file. But for testing, if ECOSTRESS_USE_AFIDS_ENV
    is defined then look for the location of this on pistol'''
    ortho_base_dir = os.path.abspath(config["StaticAncillaryFileGroup",
                                            "OrthoBase"])
    if("ECOSTRESS_USE_AFIDS_ENV" in os.environ):
        # Location on pistol, use if found, otherwise use setting in
        # run config file
        if(os.path.exists("/raid22/band5_VICAR")):
            ortho_base_dir = "/raid22"
        elif(os.path.exists("/data/smyth/Landsat/band5_VICAR")):
            ortho_base_dir = "/data/smyth/Landsat"
    return ortho_base_dir

def band_to_landsat_band(lband):
    if(lband == 1):
        return geocal.Landsat7Global.BAND1
    elif(lband == 2):
        return geocal.Landsat7Global.BAND2
    elif(lband == 3):
        return geocal.Landsat7Global.BAND3
    elif(lband == 4):
        return geocal.Landsat7Global.BAND4
    elif(lband == 5):
        return geocal.Landsat7Global.BAND5
    elif(lband == 61):
        return geocal.Landsat7Global.BAND61
    elif(lband == 62):
        return geocal.Landsat7Global.BAND62
    elif(lband == 7):
        return geocal.Landsat7Global.BAND7
    elif(lband == 8):
        return geocal.Landsat7Global.BAND8
    else:
        raise RuntimeError("Unrecognized band number")

def create_lwm(config):
    '''Create the land water mask. In production, use the directory passed
    in by the configuration file. But for testing if the special environment
    variable ECOSTRESS_USE_AFIDS_ENV is defined then look for the data at 
    the standard location on pistol.'''
    srtm_lwm_dir = os.path.abspath(config["StaticAncillaryFileGroup",
                                          "SRTMLWMDir"])
    if("ECOSTRESS_USE_AFIDS_ENV" in os.environ):
        # Location on pistol, use if found, otherwise use setting in
        # run config file
        if(os.path.exists("/raid27/tllogan/all_lwm_links")):
            srtm_lwm_dir = "/raid27/tllogan/all_lwm_links"
    lwm = geocal.SrtmLwmData(srtm_lwm_dir, False)
    return lwm
    
def setup_spice(config):
    '''Set up SPICE. In production, we use the directory passed in by 
    configuration file. However, for testing if the special environment 
    variable ECOSTRESS_USE_AFIDS_ENV is defined then we use the value passed
    in from the environment.'''
    spice_data = os.path.abspath(config["StaticAncillaryFileGroup",
                                        "SpiceDataDir"])
    if("ECOSTRESS_USE_AFIDS_ENV" not in os.environ):
        os.environ["SPICEDATA"] = spice_data
        
def create_orbit_raw(config, pos_off=None,
                     extrapolation_pad = 5, large_gap = 10):
    '''Create orbit from L1A_RAW_ATT file'''
    # Spice is needed to work with the orbit data.
    setup_spice(config)
    orbfname = os.path.abspath(config["TimeBasedFileGroup", "L1A_RAW_ATT"])
    # Create orbit.
    if(pos_off is not None):
        orb = EcostressOrbit(orbfname, pos_off, extrapolation_pad, large_gap)
    else:
        orb = EcostressOrbit(orbfname, extrapolation_pad, large_gap)
    return orb

def create_time_table(fname, mirror_rpm, frame_time, time_offset=0):
    '''Create the time table using the data from the given input.'''
    return EcostressTimeTable(fname, mirror_rpm, frame_time, time_offset)

def create_scan_mirror(fname, max_encoder_value, first_encoder_value_0,
                       second_encoder_value_0, instrument_to_sc_euler,
                       first_angle_per_encoder_value,
                       second_angle_per_encoder_value):
    '''Create the scan mirror'''
    ev = h5py.File(fname, "r")["/FPIEencoder/EncoderValue"][:]
    sm = EcostressScanMirror(ev, max_encoder_value, first_encoder_value_0,
                             second_encoder_value_0,
                             instrument_to_sc_euler[0],
                             instrument_to_sc_euler[1],
                             instrument_to_sc_euler[2],
                             first_angle_per_encoder_value,
                             second_angle_per_encoder_value)
    return sm

def is_day(igc):
    '''Determine if the center pixel of the igc is in day or night, defined
    by having the solar elevation > 0'''
    ic = geocal.ImageCoordinate(igc.number_line/2,igc.number_sample/2)
    slv = geocal.CartesianFixedLookVector.solar_look_vector(igc.pixel_time(ic))
    gpt = igc.ground_coordinate(ic)
    sol_elv = 90 - geocal.LnLookVector(slv,gpt).view_zenith
    return sol_elv > 0
    
def aster_radiance_scale_factor():
    '''Return the ASTER scale factors. This is for L1T data, found at
    https://lpdaac.usgs.gov/dataset_discovery/aster/aster_products_table/ast_l1t
    Our mosiac actually had adjustments made to make a clean mosaic, but this
    should be a reasonable approximation for going from the pixel integer data
    to radiance data in W/m^2/sr/um.'''
    return [1.688, 1.415, 0.862, 0.2174, 0.0696, 0.0625, 0.0597, 0.0417, 0.0318,
            6.882e-3, 6.780e-3, 6.590e-3, 5.693e-3, 5.225e-3]

def ecostress_to_aster_band():
    '''This is the mapping from the ASTER bands to the ECOSTRESS bands. Note that
    these aren't exact, these are just the closest match. There is no match
    for the 12.05 micron ecostress band, we reuse the 10.95 - 11.65 band. These
    band numbers are 1 based (matching the ASTER documentation).'''
    return [4, 10, 11, 12, 14, 14]

def ecostress_radiance_scale_factor(band):
    '''Not sure what we will use here, right now we use the ASTER scale. Probably
    be something like this, since the dynamic range is somewhat similar. But in
    any case, for testing this is what we use.

    band is 0 based.
    '''
    return aster_radiance_scale_factor()[ecostress_to_aster_band()[band]-1]

def time_to_file_string(acquisition_time):
    '''Return the portion of the ecostress filename based on the data acquisition 
    date and time'''
    y,m,d,h,min, sec, *rest = re.split(r'[-T:.]', str(acquisition_time))
    return y + m + d + "T" + h + min + sec

def time_split(t):
    '''Split a time into date and time, which we need to do for some of the
    metadata fields. Returns date, time'''
    mt = re.match(r'(.*)T(.*)Z', str(t))
    return mt.group(1), mt.group(2)
    
def ecostress_file_name(product_type, orbit, scene, acquisition_time,
                        end_time = None,
                        build = "0100", version = "01", extension=".h5",
                        intermediate=False):
    '''Create an ecostress file name from the given components.'''
    if(intermediate):
        front=""
    else:
        front="ECOSTRESS_"
    if(product_type == "L0B"):
        return "%s%s_%05d_%s_%s_%s%s" % \
            (front, product_type, orbit, time_to_file_string(acquisition_time),
             build, version, extension)
    elif(product_type == "Scene"):
        return "%s%s_%05d_%s_%s%s" % \
            (front, product_type, orbit,
             time_to_file_string(acquisition_time), 
             time_to_file_string(end_time), extension)
    elif(scene is None):
        # Special handling for the couple of orbit based files
        return "%s%s_%05d_%s_%s_%s%s" % \
            (front, product_type, orbit,
             time_to_file_string(acquisition_time), build,
             version, extension)
    else:
        return "%s%s_%05d_%03d_%s_%s_%s%s" % \
            (front, product_type, orbit, scene,
             time_to_file_string(acquisition_time), build,
             version, extension)
                                                   

def process_run(exec_cmd, out_fh = None, quiet = False):
    '''This is like subprocess.run, but allowing a unix like 'tee' where
    we write the output to a log file and/or stdout.

    The command (which should be a standard array) is run, and the output
    is always returned. In addition, the output is written to the given
    out_fh is supplied, and to stdout if "quiet" is not True.
    '''
    process = subprocess.Popen(exec_cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    stdout = b''
    while(True):
        output = process.stdout.readline()
        if output == b'' and process.poll() is not None:
            break
        if output:
            stdout = stdout + output
            if(not quiet):
                print(output.strip().decode('utf-8'))
                sys.stdout.flush()
            if(out_fh):
                print(output.strip().decode('utf-8'), file=out_fh)
                out_fh.flush()
    if(process.poll() != 0):
        raise subprocess.CalledProcessError(process.poll(), exec_cmd,
                                            output=stdout)
    return stdout

def orbit_from_metadata(fname):
    '''Read the standard metadata from the given file to return the orbit,
    scene, and acquisition_time for the given file.'''
    fin = h5py.File(fname, "r")
    onum = fin["/StandardMetadata/StartOrbitNumber"].value
    sid = fin["/StandardMetadata/SceneID"].value
    bdate = fin["/StandardMetadata/RangeBeginningDate"].value
    btime = fin["/StandardMetadata/RangeBeginningTime"].value
    acquisition_time = geocal.Time.parse_time("%sT%sZ" % (bdate, btime))
    return int(onum), int(sid), acquisition_time

def determine_rotated_map_igc(igc, mi):
    '''Rotate the given MapInfo so that it follows the path of the igc
    (which should be something like the minimum gore). We don't get
    the full coverage right here, but if you then use this in something
    like Resampler the coverage can be determined. This creates a rotated
    coordinate system where the center pixel at the start and ending line of
    the igc have a constant x value and varying y value, with the first line
    have the larger y value (e.g, if the rotation was 0 and y was latitude, we
    would have the larger latitude for the first line)'''
    gc1 = igc.ground_coordinate(geocal.ImageCoordinate(0, igc.number_sample / 2))
    gc2 = igc.ground_coordinate(geocal.ImageCoordinate(igc.number_line - 1,
                                                       igc.number_sample / 2))
    return determine_rotated_map(gc1, gc2, mi)

def determine_rotated_map(gc1, gc2, mi):
    '''Rotate the given MapInfo so that it follows the path of the igc
    (which should be something like the minimum gore). We don't get
    the full coverage right here, but if you then use this in something
    like Resampler the coverage can be determined. This creates a rotated
    coordinate system where the center pixel at the start and ending line of
    the igc have a constant x value and varying y value, with the first line
    have the larger y value (e.g, if the rotation was 0 and y was latitude, we
    would have the larger latitude for the first line)'''
    x1, y1 = mi.coordinate(gc1)
    x2, y2 = mi.coordinate(gc2)
    a = math.atan2(x1 - x2, y1 - y2)
    rot = np.array([[math.cos(a), -math.sin(a)],[math.sin(a),math.cos(a)]])
    p = mi.transform
    pm = np.array([[p[1], p[2]],[p[4], p[5]]])
    pm2 = np.matmul(rot,pm)
    mi2 = geocal.MapInfo(mi.coordinate_converter,
                      np.array([p[0],pm2[0,0],pm2[0,1],p[3],pm2[1,0],pm2[1,1]]),
                      mi.number_x_pixel, mi.number_y_pixel, mi.is_point)
    # In general, mi2 will cover invalid lat/lon. Just pull in to a reasonable
    # area, we handling the actual cover later
    mi2 = mi2.cover([geocal.Geodetic(10,10),geocal.Geodetic(20,20)])
    s = mi.resolution_meter / mi2.resolution_meter
    mi2 = mi2.scale(s, s)
    return mi2

__all__ = ["create_dem", "ortho_base_directory", "band_to_landsat_band",
           "create_lwm", "setup_spice",
           "create_orbit_raw", "create_time_table", "create_scan_mirror",
           "is_day", "aster_radiance_scale_factor", "ecostress_to_aster_band",
           "ecostress_radiance_scale_factor", "time_to_file_string",
           "time_split", "ecostress_file_name", "process_run",
           "orbit_from_metadata", "determine_rotated_map", "determine_rotated_map_igc"]
