from .gaussian_stretch import gaussian_stretch
import geocal  # type: ignore
from ecostress_swig import Resampler, fill_value_threshold  # type: ignore
import os
import subprocess
import copy
import math
import numpy as np
import scipy  # type: ignore


class L1bGeoGenerateKmz(object):
    """This generates a L1B Geo KMZ file. Right now we leverage off of
    the L1bGeoGenerate class, since most of the work is the same. We could
    break this connection if it is ever needed, but at least currently
    we always generate the L1bGeoGenerate and optionally do the
    L1bGeoGenerateKmz.

    Like L1bGeoGenerate, to actually generate you should execute the "run"
    command. Make sure the L1bGeoGenerate run has been executed first, we rely
    on data generated there."""

    def __init__(
        self,
        l1b_geo_generate,
        l1b_rad,
        output_name,
        local_granule_id=None,
        band_list=[4, 3, 1],
        use_jpeg=False,
        resolution=70,
        number_subpixel=3,
        thumbnail_size=[0, 0],
    ):
        """Thumbnail size is in pixels, x and y. If one of the
        sizes is 0 then we hold the aspect ratio to 1. If both are 0, then
        we use the size of final kmz layer"""
        self.l1b_geo_generate = l1b_geo_generate
        self.l1b_rad = l1b_rad
        self.band_list = band_list
        self.use_jpeg = use_jpeg
        self.resolution = resolution
        self.number_subpixel = number_subpixel
        self.output_name = output_name
        if local_granule_id:
            self.local_granule_id = local_granule_id
        else:
            self.local_granule_id = os.path.basename(output_name)
        self.thumbnail_size = thumbnail_size

    def run(self):
        # Note short name is L1B_KMZ_MAP, although we don't actually
        # generate standard metadata
        # m = self.l1b_geo_generate.m.copy_new_file(fout,
        #                         self.local_granule_id, "L1B_KMZ_MAP")

        # Generate map data
        mi = geocal.cib01_mapinfo(self.resolution)
        # Most of the time, we have no fill values so just do a normal zoom
        if(np.count_nonzero(self.l1b_geo_generate.lat < fill_value_threshold) == 0 and
           np.count_nonzero(self.l1b_geo_generate.lon < fill_value_threshold) == 0):
            lat = scipy.ndimage.interpolation.zoom(
                self.l1b_geo_generate.lat, self.number_subpixel, order=2
            )
            lon = scipy.ndimage.interpolation.zoom(
                self.l1b_geo_generate.lon, self.number_subpixel, order=2
            )
        else:
            # But if we do, have special handling
            #
            # Order here of "1" is bilinear. We can't use higher order since we
            # may have missing data and this gets spread out with higher order
            # interpolation. As an easy way of handling this, we set
            # missing data as extremely negative value
            latv = self.l1b_geo_generate.lat.copy()
            lonv = self.l1b_geo_generate.lon.copy()
            latv[latv < fill_value_threshold] = -1e20
            lonv[lonv < fill_value_threshold] = -1e20
            lat = scipy.ndimage.interpolation.zoom(
                self.l1b_geo_generate.lat, self.number_subpixel, order=1
            )
            lon = scipy.ndimage.interpolation.zoom(
                self.l1b_geo_generate.lon, self.number_subpixel, order=1
            )
        res = Resampler(lon, lat, mi, self.number_subpixel, False)
        cmd_merge = ["gdalbuildvrt", "-q", "-separate", "map_scaled.vrt"]
        for b in self.band_list:
            ras = geocal.GdalRasterImage(
                'HDF5:"%s"://Radiance/radiance_%d' % (self.l1b_rad, b)
            )
            data = res.resample_field(ras)
            data_scaled = gaussian_stretch(data)
            fname = "map_b%d_scaled.img" % b
            d = geocal.mmap_file(fname, res.map_info, nodata=0.0, dtype=np.uint8)
            d[:] = data_scaled
            d = None
            cmd_merge.append(fname)
        subprocess.run(cmd_merge)
        cmd = [
            "gdal_translate",
            "-of",
            "KMLSUPEROVERLAY",
            "map_scaled.vrt",
            self.output_name,
        ]
        if not self.use_jpeg:
            cmd.extend(["-co", "FORMAT=PNG"])
        subprocess.run(cmd)
        thumbnail_file = os.path.splitext(self.output_name)[0] + "_thumbnail.jpg"
        thumbnail_size = copy.copy(self.thumbnail_size)
        if thumbnail_size[0] == 0 and thumbnail_size[1] == 0:
            nline = geocal.GdalRasterImage("map_scaled.vrt").number_line
            nsamp = geocal.GdalRasterImage("map_scaled.vrt").number_sample
            while nline > 256 or nsamp > 256:
                thumbnail_size = [nsamp, nline]
                nline = int(math.floor(nline / 2))
                nsamp = int(math.floor(nsamp / 2))
        cmd = [
            "gdal_translate",
            "-of",
            "jpeg",
            "-outsize",
            str(thumbnail_size[0]),
            str(thumbnail_size[1]),
            "map_scaled.vrt",
            thumbnail_file,
        ]
        subprocess.run(cmd)


__all__ = ["L1bGeoGenerateKmz"]
