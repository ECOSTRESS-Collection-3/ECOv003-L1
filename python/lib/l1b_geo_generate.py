from geocal import *
import h5py

class L1bGeoGenerate(object):
    '''This generate a L1B geo output file from a given
    ImageGroundConnection. I imagine we will modify this as time
    goes on, this is really just a placeholder.
    '''
    def __init__(self, igc, output_name):
        '''Create a L1bGeoGenerate with the given ImageGroundConnection
        and output file name. To actually generate, execute the 'run'
        command.'''
        self.igc = igc
        self.output_name = output_name

    def loc(self, start_line = 0,
            number_line = -1,
            number_integration_step = 1,
            dem_resolution = 100, 
            max_height=10e3,
            start_sample = 0,
            number_sample = -1):
        '''Determine locations'''
        rcast = IgcRayCaster(self.igc, start_line,
                             number_line, number_integration_step,
                             dem_resolution, max_height, start_sample,
                             number_sample)
        print "Have %d positions to calculate" % rcast.number_position
        lat = np.empty((rcast.number_position, rcast.number_sample))
        lon = np.empty((rcast.number_position, rcast.number_sample))
        height = np.empty((rcast.number_position, rcast.number_sample))
        i = 0
        while True:
            r = rcast.next_position()
            ln = rcast.current_position - rcast.start_position
            for j in range(r.shape[1]):
                pt = Ecr(*r[0,j,0,0,0,:])
                lat[ln, j] = pt.latitude
                lon[ln, j] = pt.longitude
                height[ln, j] = pt.height_reference_surface
            i += 1
            if(i % 100 ==0):
                print "Done with position %d" % i
            if(rcast.last_position):
                break
        return lat, lon, height

    def run(self, start_line = 0,
            number_line = -1,
            number_integration_step = 1,
            dem_resolution = 100, 
            max_height=10e3,
            start_sample = 0,
            number_sample = -1):
        '''Do the actual generation of data.'''
        lat, lon, height = \
            self.loc(start_line, number_line,
                     number_integration_step, dem_resolution, max_height, 
                     start_sample, number_sample)
        fout = h5py.File(self.output_name, "w")
        g = fout.create_group("L1bGeo")
        g.attrs["Projection"] = '''\
The latitude, longitude, and height are relative to the WGS-84
ellipsoid. Specifically the projection used is described by
the Well-Known Text (WKT):

GEOGCS["WGS 84",
    DATUM["WGS_1984",
        SPHEROID["WGS 84",6378137,298.257223563,
            AUTHORITY["EPSG","7030"]],
        AUTHORITY["EPSG","6326"]],
    PRIMEM["Greenwich",0],
    UNIT["degree",0.0174532925199433],
    AUTHORITY["EPSG","4326"]]
'''
        g.attrs["Projection_WKT"] = '''\
GEOGCS["WGS 84",
    DATUM["WGS_1984",
        SPHEROID["WGS 84",6378137,298.257223563,
            AUTHORITY["EPSG","7030"]],
        AUTHORITY["EPSG","6326"]],
    PRIMEM["Greenwich",0],
    UNIT["degree",0.0174532925199433],
    AUTHORITY["EPSG","4326"]]
'''
        t = g.create_dataset("latitude", data=lat)
        t.attrs["Units"] = "degrees"
        t = g.create_dataset("longitude", data=lon)
        t.attrs["Units"] = "degrees"
        t = g.create_dataset("height", data=height/1e3)
        t.attrs["Units"] = "km"
        
