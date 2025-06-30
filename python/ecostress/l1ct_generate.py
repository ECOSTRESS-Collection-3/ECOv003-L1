import geocal  # type: ignore
from ecostress_swig import (
    fill_value_threshold,
    Resampler,
    coordinate_convert,
    write_data,
    write_gdal,
    set_fill_value,
)  # type: ignore
import h5py
import scipy
import numpy as np
import math
from loguru import logger
from pathlib import Path
from zipfile import ZipFile
import shutil

class L1ctGenerate:
    """Produce L1CT tiles"""

    def __init__(
        self,
        l1b_geo,
        l1b_rad,
        l1_osp_dir,
        output_pattern,
        inlist,
        resolution=70,
        number_subpixel=3,
        run_config=None,
        collection_label="ECOSTRESS",
        build_id="0.30",
        pge_version="0.30",
    ):
        """The output pattern should leave a portion called "TILE" in the name, that
        we fill in. Also leave the extension off, so a name like:

        ECOv002_L1CT_RAD_35544_007_TILE_20241012T201510_0713_01
        """
        self.l1b_geo = l1b_geo
        self.l1b_rad = l1b_rad
        self.output_pattern = output_pattern
        self.l1_osp_dir = l1_osp_dir
        self.resolution = resolution
        self.number_subpixel = number_subpixel
        self._utm_coor = {}
        self.use_file_cache = False
        self.run_config = run_config
        self.inlist = inlist
        self.collection_label = collection_label
        self.build_id = build_id
        self.pge_version = pge_version

    def run(self, pool=None):
        fin_geo = h5py.File(self.l1b_geo, "r")
        self.lat = fin_geo["Geolocation/latitude"][:, :]
        self.lon = fin_geo["Geolocation/longitude"][:, :]
        sfile = geocal.ShapeFile(self.l1_osp_dir / "sentinel_tile.shp")
        lay = sfile["sentinel_tile"]
        lay.set_filter_rect(
            self.lon[self.lon > fill_value_threshold].min(),
            self.lat[self.lat > fill_value_threshold].max(),
            self.lon[self.lon > fill_value_threshold].max(),
            self.lat[self.lat > fill_value_threshold].min(),
        )
        # Calculate all the UTM. We do this before starting the parallel step
        if pool is None:
            _ = list(map(self.process_tile, [shp for shp in lay]))
        else:
            self.use_file_cache = True
            shp_dict_list = []
            for shp in lay:
                owrap, x, y = self.utm_coor(shp["epsg"])
                d = {}
                for ky in ("tile_id", "epsg", "xstart", "ystart"):
                    d[ky] = shp[ky]
                shp_dict_list.append(d)
            self._utm_coor = {}
            _ = pool.map(self.process_tile, shp_dict_list)

    def utm_coor(self, epsg):
        """Calculate utm coordinate. We can optional save/load from disk if needed - this
        is to support multiprocessing"""
        if epsg not in self._utm_coor:
            cache_fname = Path(f"epsg_{epsg}.npy")
            owrap = geocal.OgrWrapper.from_epsg(epsg)
            if self.use_file_cache and cache_fname.exists():
                with open(cache_fname, "rb") as f:
                    x = np.load(f)
                    y = np.load(f)
                return (owrap, x, y)
            else:
                logger.info(f"Calculating UTM coordinates for epsg {epsg}")
                x = self.lat.copy()
                y = self.lon.copy()
                res = coordinate_convert(x.reshape(x.size), y.reshape(y.size), owrap)
                x[:, :] = res[:, 0].reshape(x.shape)
                y[:, :] = res[:, 1].reshape(y.shape)
                # Make sure fill values are negative enough that is clear we
                # should ignore them, even after interpolation
                x[self.lat < fill_value_threshold] = -1e20
                x[self.lon < fill_value_threshold] = -1e20
                y[self.lat < fill_value_threshold] = -1e20
                y[self.lon < fill_value_threshold] = -1e20
                # Order 1 is bilinear interpolation
                x = scipy.ndimage.interpolation.zoom(x, self.number_subpixel, order=1)
                y = scipy.ndimage.interpolation.zoom(y, self.number_subpixel, order=1)
                if self.use_file_cache:
                    with open(cache_fname, "wb") as f:
                        np.save(f, x)
                        np.save(f, y)
                    return (owrap, x, y)
                else:
                    self._utm_coor[epsg] = (owrap, x, y)
        return self._utm_coor[epsg]

    def process_tile(self, shp):
        logger.info(f"Processing {shp['tile_id']}")
        owrap, x, y = self.utm_coor(shp["epsg"])
        # Tile is exactly 109800, but depending on resolution we might be slightly
        # smaller since we need an even number of pixels
        npix = math.floor(109800 / self.resolution)
        mi = geocal.MapInfo(
            geocal.OgrCoordinateConverter(owrap),
            shp["xstart"],
            shp["ystart"],
            shp["xstart"] + self.resolution * npix,
            shp["ystart"] - self.resolution * npix,
            npix,
            npix,
        )
        res = Resampler(x, y, mi, self.number_subpixel, True)
        # Free up memory
        x = None
        y = None
        logger.info("Done with Resampler init")
        # Note in general we may get tiles in our search of the shape file that
        # don't actually end up having any data once we look in detail. Just
        # skip tiles that will be empty
        if res.empty_resample():
            logger.info("Tile is empty, skipping")
            logger.info(f"Done with {shp['tile_id']}")
            res = None
            return False
        dirname = Path(self.output_pattern.replace("TILE", shp["tile_id"]))
        geocal.makedirs_p(dirname)
        for b in range(1, 6):
            logger.info(f"Doing radiance band {b} - {shp['tile_id']}")
            data_in = geocal.GdalRasterImage(
                f'HDF5:"{self.l1b_rad}"://Radiance/radiance_{b}'
            )
            data = res.resample_field(data_in, 1.0, False, np.nan)
            # COG can only create on copy, so we first create this in memory and
            # then write out.
            f = geocal.GdalRasterImage(
                "",
                "MEM",
                mi,
                1,
                geocal.GdalRasterImage.Float32)
            set_fill_value(f, np.nan)
            write_data(f, data)
            write_gdal(str(dirname / f"{dirname}_radiance_{b}.tif"), "COG",
                       f, "BLOCKSIZE=256 COMPRESS=DEFLATE")
            f.close()
        for b in range(1, 6):
            # GeoCal doesn't support the dqi type. We could update geocal,
            # but no strong reason to. Just read into memory
            logger.info(f"Doing DQI band {b} - {shp['tile_id']}")
            din = h5py.File(self.l1b_rad)[f"Radiance/data_quality_{b}"][:, :]
            data_in = geocal.MemoryRasterImage(din.shape[0], din.shape[1])
            data_in.write(0, 0, din)
            data = res.resample_dqi(data_in).astype(int)
            # COG can only create on copy, so we first create this in memory and
            # then write out.
            f = geocal.GdalRasterImage(
                "",
                "MEM",
                mi,
                1,
                geocal.GdalRasterImage.UInt16
            )
            f.write(0, 0, data)
            write_gdal(str(dirname / f"{dirname}_data_quality_{b}.tif"), "COG",
                       f, "BLOCKSIZE=256 COMPRESS=DEFLATE")
            f.close()
        res = None
        # Create zip file
        with ZipFile(f"{dirname}.zip", "w") as fh:
            for filename in Path(dirname).glob("*"):
                fh.write(filename)
        shutil.rmtree(dirname)
                
        logger.info(f"Done with {shp['tile_id']}")
        return True

        # breakpoint()
        # Make sure fill values are negative enough that is clear we
        # should ignore them, even after interpolation
        # latv[latv < fill_value_threshold] = -1e20
        # lonv[lonv < fill_value_threshold] = -1e20
        # Order 1 is bilinear interpolation
        # lat = scipy.ndimage.interpolation.zoom(
        #    latv, self.number_subpixel, order=1
        # )
        # lon = scipy.ndimage.interpolation.zoom(
        #    lonv, self.number_subpixel, order=1
        # )
        # res = Resampler(lon, lat, mi, self.number_subpixel, False)
        # logger.info("Done with Resampler init")
        # mi = res.map_info

        # TODO Make sure to update bounding box stuff in output metadata
        # TODO Put into place, I think we need to handle this with something
        # other than write_standard_metadata
        # m = self.l1b_geo_generate.m.copy_new_file(
        #    fout, self.local_granule_id, "ECO_L1CG_RAD"
        # )


__all__ = ["L1ctGenerate"]
