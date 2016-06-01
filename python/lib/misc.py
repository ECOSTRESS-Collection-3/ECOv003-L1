# This is various miscellaneous routines that don't fit elsewhere
from geocal import *

def aster_radiance_scale_factor():
    '''Return the ASTER scale factors. This is for L1T data, found at
    https://lpdaac.usgs.gov/dataset_discovery/aster/aster_products_table/ast_l1t
    Our mosiac actually had adjustments made to make a clean mosaic, but this
    should be a reasonable approximation for going from the pixel integer data
    to radaince data in W/m^2/sr/um.'''
    return [1.688, 1.415, 0.862, 0.2174, 0.0696, 0.0625, 0.0597, 0.0417, 0.0318,
            6.882e-3, 6.780e-3, 6.590e-3, 5.693e-3, 5.225e-3]

def ecostress_to_aster_band():
    '''This is the mapping from the ASTER bands to the ECOSTRESS bands. Note that
    these aren't exact, these are just the closest match. There is no match
    for the 12.05 micron ecostress band, we reuse the 10.95 - 11.65 band. These
    band numbers are 1 based (matching the ASTER documentation).'''
    return [14, 14, 12, 11, 10, 4]

def time_to_file_string(acquisition_time):
    '''Return the portion of the ecostress filename based on the data acquisition 
    date and time'''
    y,m,d,h,min, sec, *rest = re.split(r'[-T:.]', str(acquisition_time))
    return y + m + d + "_" + h + min + sec

def ecostress_file_name(product_type, orbit, scene, acquisition_time,
                        build = "0100", version = "01"):
    '''Create an ecostress file name from the given components.'''
    if(orbit is None):
        # Special handling for the L0 data
        return "ECOSTRESS_%s_%s_%s_%s.h5" % \
            (product_type, time_to_file_string(acquisition_time), build,
             version)
    elif(scene is None):
        # Special handling for the couple of orbit based files
        return "ECOSTRESS_%s_%05d_%s_%s_%s.h5" % \
            (product_type, orbit, time_to_file_string(acquisition_time), build,
             version)
    else:
        return "ECOSTRESS_%s_%05d_%03d_%s_%s_%s.h5" % \
            (product_type, orbit, scene, time_to_file_string(acquisition_time), build,
             version)
                                                   
