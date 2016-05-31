# This is various miscellaneous routines that don't fit elsewhere
from geocal import *

def time_to_file_string(acquisition_time):
    '''Return the portion of the ecostress filename based on the data acquisition 
    date and time'''
    y,m,d,h,min, sec, *rest = re.split(r'[-T:.]', str(acquisition_time))
    return y + m + d + "_" + h + min + sec

def ecostress_file_name(product_type, orbit, scene, acquisition_time,
                        build = "0100", version = "01"):
    '''Create an ecostress file name from the given components.'''
    return "ECOSTRESS_%s_%05d_%03d_%s_%s_%s.h5" % \
        (product_type, orbit, scene, time_to_file_string(acquisition_time), build,
         version)
                                                   
