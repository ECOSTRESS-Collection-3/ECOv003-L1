# This is various miscellaneous routines that don't fit elsewhere
from geocal import *
import re
import subprocess
import h5py

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
    return [14, 14, 12, 11, 10, 4]

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
    if(orbit is None):
        # Special handling for the L0 data
        return "%s%s_%s_%s_%s_%s%s" % \
            (front, product_type, time_to_file_string(acquisition_time),
             time_to_file_string(end_time),
             build, version, extension)
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
    acquisition_time = Time.parse_time("%sT%sZ" % (bdate, btime))
    return int(onum), int(sid), acquisition_time
    
