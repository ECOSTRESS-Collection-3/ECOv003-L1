import geocal
from ecostress_swig import *
from .misc import determine_rotated_map_igc
import os
import h5py
import numpy as np
import scipy
import subprocess

class L1bGeoGenerateMap(object):
    '''This generates a L1B Geo map product. Right now we leverage off of
    the L1bGeoGenerate class, since most of the work is the same. We could
    break this connection if it is ever needed, but at least currently
    we always generate the L1bGeoGenerate and optionally do the 
    L1bGeoGenerateMap.

    Like L1bGeoGenerate, to actually generate you should execute the "run"
    command. Make sure the L1bGeoGenerate run has been executed first, we rely 
    on data generated there.
    
    By default, we generate a rotated map. You can instead force a north is up
    map by setting north_up to true. Likewise, default resolution is 70 meters,
    but you can modify this.
    '''
    def __init__(self, l1b_geo_generate, l1b_rad, output_name,
                 local_granule_id = None, log_fname = None,
                 resolution = 70, north_up = False, number_subpixel = 3):
        self.l1b_geo_generate = l1b_geo_generate
        self.l1b_rad = l1b_rad
        self.output_name = output_name
        if(local_granule_id):
            self.local_granule_id = local_granule_id
        else:
            self.local_granule_id = os.path.basename(output_name)
        self.log_fname = log_fname
        self.north_up = north_up
        self.resolution = resolution
        self.number_subpixel = number_subpixel

    def print_and_log(self, s):
        print(s)
        if(self.log_fname is not None):
            self.log = open(self.log_fname, "a")
            print("INFO:L1bGeoGenerateMap:%s" % s, file = self.log)
            self.log.flush()
            self.log = None

    def run(self):
        fout = h5py.File(self.output_name, "w")
        m = self.l1b_geo_generate.m.copy_new_file(fout,
                                 self.local_granule_id, "ECO1BMAP")
        m.write()
        mi = geocal.cib01_mapinfo(self.resolution)
        lat = scipy.ndimage.interpolation.zoom(self.l1b_geo_generate.lat,
                                               self.number_subpixel, order=2)
        lon = scipy.ndimage.interpolation.zoom(self.l1b_geo_generate.lon,
                                               self.number_subpixel, order=2)
        if(not self.north_up):
            mi = determine_rotated_map_igc(self.l1b_geo_generate.igc, mi)
        res = Resampler(lat, lon, mi, self.number_subpixel, False)
        self.print_and_log("Done with Resampler init")
        g = fout.create_group("Mapped")
        g2 = g.create_group("MapInformation")
        g2["README"] = \
'''We specify the Map Information by giving the Coordinate System
and a Affine GeoTransform. The Coordinate System is specified as 
OpeGIS Well Known Text strings(see for example
https://en.wikipedia.org/wiki/Well-known_text or 
http://www.gdal.org/gdal_datamodel.html). This is given in the
CoordinateSystem.

We also specify the Affine GeoTransform (as for example in
geotiff, see http://geotiff.maptools.org/spec/geotiff2.6.html or
GDAL, see http://www.gdal.org/gdal_datamodel.html). This is given
in the GeoTransform. We have:

longitude   = GT_0 + GT_1 * i + GT_2 * j
latitude    = GT_3 + GT_4 * i + GT_5 * j

Where (i,j) is the sample, line of the pixel (starting at 0) and longitude
and latitude are given in degrees.

Note that in addition, we have the latitude and longitude fields in
the file. This is completely redundant with the map projection information,
we supply these fields as a convenience for software that expects this
data. But you can directly calculate latitude and longitude from the map
information.
'''
        # Hardcoded for now, this is probably fine since we don't expect to
        # change the coordinate system
        g2["CoordinateSystem"] = \
'''GEOGCS["WGS 84",
    DATUM["WGS_1984",
        SPHEROID["WGS 84",6378137,298.257223563,
            AUTHORITY["EPSG","7030"]],
        AUTHORITY["EPSG","6326"]],
    PRIMEM["Greenwich",0],
    UNIT["degree",0.0174532925199433],
    AUTHORITY["EPSG","4326"]]
'''
        g2.create_dataset("GeoTransform", data=res.map_info.transform,
                          dtype='f8')
        lat, lon, height = res.map_values(self.l1b_geo_generate.igc.dem)
        t = g.create_dataset("latitude", data=lat, dtype='f8')
        t.attrs["Units"] = "degrees"
        t = g.create_dataset("longitude", data=lon, dtype='f8')
        t.attrs["Units"] = "degrees"
        t = g.create_dataset("height", data=height, dtype='f4')
        t.attrs["Units"] = "m"
        self.print_and_log("Done with lat, lon, height")
        # Land fraction
        for b in range(1,6):
            self.print_and_log("Doing band %d" % b)
            data_in = geocal.GdalRasterImage("HDF5:\"%s\"://Radiance/radiance_%d" % (self.l1b_rad, b))
            data = res.resample_field(data_in, 1.0, False,
                         FILL_VALUE_NOT_SEEN).astype(np.float32)
            t = g.create_dataset("radiance_%d" % b, data = data, dtype='f4',
                                 fillvalue = FILL_VALUE_NOT_SEEN)
            t.attrs.create("_FillValue", data=FILL_VALUE_NOT_SEEN,
                           dtype=t.dtype)
            t.attrs["Units"] = "W/m^2/sr/um"
            # DQI
        self.print_and_log("Doing SWIR")    
        data_in = geocal.GdalRasterImage("HDF5:\"%s\"://SWIR/swir_dn" % self.l1b_rad)
        data = res.resample_field(data_in, 1.0, False,
                                 FILL_VALUE_NOT_SEEN).astype(np.int16)
        t = g.create_dataset("swir_dn",
                             data = data,
                             fillvalue = FILL_VALUE_NOT_SEEN)
        t.attrs.create("_FillValue", data=FILL_VALUE_NOT_SEEN,
                       dtype=t.dtype)
        t.attrs["Units"] = "dimensionless"
        # Solar azimuth, solar zenith, view azimuth, view zenith
        # Create GDAL VRT file. No specific use for this, but it is
        # quick to generate and might be useful
        fout.close()
        vrtfile = os.path.splitext(self.output_name)[0] + "_gdal.vrt"
        cmd = ["gdalbuildvrt", "-separate", vrtfile]
        cmd.extend("HDF5:\"%s\"://Mapped/radiance_%d" % (self.output_name, b+1)
                   for b in range(5))
        cmd.append("HDF5:\"%s\"://Mapped/swir_dn" % self.output_name)
        cmd.append("HDF5:\"%s\"://Mapped/latitude" % self.output_name)
        cmd.append("HDF5:\"%s\"://Mapped/longitude" % self.output_name)
        cmd.append("HDF5:\"%s\"://Mapped/height" % self.output_name)
        subprocess.run(cmd)
        tstring = ",".join("{:.20e}".format(t) for t in res.map_info.transform)
        cmd=["sed", "-i", "s#</SRS>#</SRS>\\n  <GeoTransform>%s</GeoTransform>\\n  <Metadata>\\n    <MDI key=\"AREA_OR_POINT\">Area</MDI>\\n  </Metadata>#" % tstring, vrtfile]
        subprocess.run(cmd)
        
        
        
__all__ = ["L1bGeoGenerateMap"]
        
