import geocal  # type: ignore
from ecostress_swig import fill_value_threshold, Resampler, HdfEosFileHandle, HdfEosGrid, coordinate_convert  # type: ignore
import os
import h5py
import scipy
import numpy as np
import math
from loguru import logger

class L1ctGenerate:
    '''Produce L1CT tiles
    '''
    def __init__(self, l1b_geo, l1b_rad, l1_osp_dir, output_pattern, 
                 resolution=70, number_subpixel=3):
        '''The output pattern should leave a portion called "TILE" in the name, that
        we fill in. Also leave the extension off, so a name like:

        ECOv002_L1CT_RAD_35544_007_TILE_20241012T201510_0713_01
        '''
        self.l1b_geo = l1b_geo
        self.l1b_rad = l1b_rad
        self.output_pattern = output_pattern
        self.l1_osp_dir = l1_osp_dir
        self.resolution = resolution
        self.number_subpixel = number_subpixel
        self._utm_coor = {}

    def run(self):
        fin_geo = h5py.File(self.l1b_geo, "r")
        self.lat = fin_geo["Geolocation/latitude"][:,:]
        self.lon = fin_geo["Geolocation/longitude"][:,:]
        sfile = geocal.ShapeFile(self.l1_osp_dir / "sentinel_tile.shp")
        lay = sfile["sentinel_tile"]
        lay.set_filter_rect(self.lon[self.lon > fill_value_threshold].min(),
                            self.lat[self.lat > fill_value_threshold].max(),
                            self.lon[self.lon > fill_value_threshold].max(),
                            self.lat[self.lat > fill_value_threshold].min())
        for shp in lay:
            self.process_tile(shp)

    def utm_coor(self, epsg):
        if epsg not in self._utm_coor:
            logger.info(f"Calculating UTM coordinates for epsg {epsg}")
            owrap = geocal.OgrWrapper.from_epsg(epsg)
            x = self.lat.copy()
            y = self.lon.copy()
            res = coordinate_convert(x.reshape(x.size), y.reshape(y.size), owrap)
            x[:, :] = res[:,0].reshape(x.shape)
            y[:, :] = res[:,1].reshape(y.shape)
            # Make sure fill values are negative enough that is clear we
            # should ignore them, even after interpolation
            x[self.lat < fill_value_threshold] = -1e20
            x[self.lon < fill_value_threshold] = -1e20
            y[self.lat < fill_value_threshold] = -1e20
            y[self.lon < fill_value_threshold] = -1e20
            # Order 1 is bilinear interpolation
            x = scipy.ndimage.interpolation.zoom(
                x, self.number_subpixel, order=1
            )
            y = scipy.ndimage.interpolation.zoom(
                y, self.number_subpixel, order=1
            )
            self._utm_coor[epsg] = (owrap, x,y)
        return self._utm_coor[epsg]

    def process_tile(self, shp):
        logger.info(f"Processing {shp['tile_id']}")
        owrap, x, y = self.utm_coor(shp['epsg'])
        # Tile is exactly 109800, but depending on resolution we might be slightly
        # smaller since we need an even number of pixels
        npix = math.floor(109800 / self.resolution)
        mi = geocal.MapInfo(geocal.OgrCoordinateConverter(owrap),
                            shp['xstart'], shp['ystart'],
                            shp['xstart'] + self.resolution * npix,
                            shp['ystart'] - self.resolution * npix,
                            npix, npix)
        res = Resampler(x, y, mi, self.number_subpixel, True)
        logger.info("Done with Resampler init")
        # Note in general we may get tiles in our search of the shape file that
        # don't actually end up having any data once we look in detail. Just
        # skip tiles that will be empty
        if(res.empty_resample()):
            logger.info("Tile is empty, skipping")
            return
        
        #breakpoint()
        # Make sure fill values are negative enough that is clear we
        # should ignore them, even after interpolation
        #latv[latv < fill_value_threshold] = -1e20
        #lonv[lonv < fill_value_threshold] = -1e20
        # Order 1 is bilinear interpolation
        #lat = scipy.ndimage.interpolation.zoom(
        #    latv, self.number_subpixel, order=1
        #)
        #lon = scipy.ndimage.interpolation.zoom(
        #    lonv, self.number_subpixel, order=1
        #)
        #res = Resampler(lon, lat, mi, self.number_subpixel, False)
        #logger.info("Done with Resampler init")
        #mi = res.map_info
            

        # TODO Make sure to update bounding box stuff in output metadata
        # TODO Put into place, I think we need to handle this with something
        # other than write_standard_metadata
        #m = self.l1b_geo_generate.m.copy_new_file(
        #    fout, self.local_granule_id, "ECO_L1CG_RAD"
        #)

    
__all__ = ["L1ctGenerate"]
