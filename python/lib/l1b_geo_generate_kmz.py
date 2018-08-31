import geocal
from ecostress_swig import *

class L1bGeoGenerateKmz(object):
    '''This generates a L1B Geo KMZ file. Right now we leverage off of
    the L1bGeoGenerate class, since most of the work is the same. We could
    break this connection if it is ever needed, but at least currently
    we always generate the L1bGeoGenerate and optionally do the 
    L1bGeoGenerateKmz.

    Like L1bGeoGenerate, to actually generate you should execute the "run"
    command. Make sure the L1bGeoGenerate run has been executed first, we rely 
    on data generated there.'''
    def __init__(self, l1b_geo_generate, output_name,
                 local_granule_id = None, log_fname = None):
        self.l1b_geo_generate = l1b_geo_generate
        self.output_name = output_name
        self.local_granule_id = local_granule_id
        self.log_fname = log_fname
        
