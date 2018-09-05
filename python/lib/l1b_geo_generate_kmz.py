from .gaussian_stretch import gaussian_stretch
import geocal
from ecostress_swig import *
import os
import subprocess

class L1bGeoGenerateKmz(object):
    '''This generates a L1B Geo KMZ file. Right now we leverage off of
    the L1bGeoGenerate class, since most of the work is the same. We could
    break this connection if it is ever needed, but at least currently
    we always generate the L1bGeoGenerate and optionally do the 
    L1bGeoGenerateKmz.

    Like L1bGeoGenerate, to actually generate you should execute the "run"
    command. Make sure the L1bGeoGenerate run has been executed first, we rely 
    on data generated there.'''
    def __init__(self, l1b_geo_generate, l1b_rad, output_name,
                 local_granule_id = None, log_fname = None,
                 band_list = [4,3,1],
                 use_jpeg = False,
                 resolution = 70, number_subpixel = 3):
        self.l1b_geo_generate = l1b_geo_generate
        self.l1b_rad = l1b_rad
        self.band_list = band_list
        self.use_jpeg = use_jpeg
        self.resolution = resolution
        self.number_subpixel = number_subpixel
        self.output_name = output_name
        if(local_granule_id):
            self.local_granule_id = local_granule_id
        else:
            self.local_granule_id = os.path.basename(output_name)
        self.log_fname = log_fname
        
    def run(self):
        # Note short name is L1B_KMZ_MAP, although we don't actually
        # generate standard metadata
        #m = self.l1b_geo_generate.m.copy_new_file(fout,
        #                         self.local_granule_id, "L1B_KMZ_MAP")

        # Generate map data
        mi = geocal.cib01_mapinfo(self.resolution)
        lat = self.l1b_geo_generate.lat
        lon = self.l1b_geo_generate.lon
        res = Resampler(lat, lon, mi, self.number_subpixel, False)
        cmd_merge = ["gdalbuildvrt", "-q", "-separate", "map_scaled.vrt"]
        for b in self.band_list:
            ras = geocal.GdalRasterImage("HDF5:\"%s\"://Radiance/radiance_%d" %
                                         (self.l1b_rad, b))
            data = res.resample_field(ras)
            data_scaled = gaussian_stretch(data)
            fname = "map_b%d_scaled.img" % b
            f = geocal.VicarRasterImage(fname, res.map_info)
            f["NODATA"] = 0.0
            f.write(0,0,data_scaled)
            f.close()
            cmd_merge.append(fname)
        subprocess.run(cmd_merge)
        cmd = ["gdal_translate", "-of", "KMLSUPEROVERLAY", "map_scaled.vrt",
               self.output_name]
        if(not self.use_jpeg):
            cmd.extend(["-co", "FORMAT=PNG"])
        subprocess.run(cmd)
        thumbnailfile = os.path.splitext(self.output_name)[0] + "_thumbnail"
        if(self.use_jpeg):
            ext = "jpg"
            subprocess.run("unzip -p %s 0/0/0.%s | cat > %s.%s" % (self.output_name, ext, thumbnailfile, ext), shell=True)
        else:
            ext = "png"
            subprocess.run("unzip -p %s 0/0/0.%s | convert - %s.%s" % (self.output_name, ext, thumbnailfile, "jpg"), shell=True)

__all__ = ["L1bGeoGenerateKmz"]
    
