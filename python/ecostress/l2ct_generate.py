from __future__ import annotations
import geocal  # type: ignore
from ecostress_swig import (  # type: ignore
    fill_value_threshold,
    FILL_VALUE_BAD_OR_MISSING,
    Resampler,
    coordinate_convert,
    write_data,
    write_gdal,
    gdal_band,
    set_fill_value,
    to_proj4,
    MemoryRasterImageFloat,
)
from .l1ct_write_standard_metadata import L1ctWriteStandardMetadata
import h5py  # type: ignore
import scipy  # type: ignore
import numpy as np
import math
from loguru import logger
from pathlib import Path
from zipfile import ZipFile
import shutil
import os
import subprocess
import matplotlib.pyplot as plt
import typing

if typing.TYPE_CHECKING:
    from multiprocessing.pool import Pool
    from .run_config import RunConfig


class L2ctGenerate:
    """Produce L2CT tiles. This will likely get replaced and pulled out of Level 1,
    but for now have this here."""

    def __init__(
        self,
        l1cg: str | os.PathLike[str],
        l2cg_lste: str | os.PathLike[str],
        l1_osp_dir: str | os.PathLike[str],
        output_pattern: str | os.PathLike[str],
        inlist: list[str],
        resolution: float = 70,
        number_subpixel: int = 3,
        run_config: RunConfig | None = None,
        collection_label: str = "ECOSTRESS",
        build_id: str = "0.30",
        pge_version: str = "0.30",
        browse_size: int = 1080,
    ) -> None:
        """The output pattern should leave a portion called "TILE" in the name, that
        we fill in. Also leave the extension off, so a name like:

        ECOv002_L2T_LSTE_35544_007_TILE_20241012T201510_0713_01
        """
        self.l1cg = Path(l1cg)
        self.l2cg_lste = Path(l2cg_lste)
        self.output_pattern = output_pattern
        self.l1_osp_dir = Path(l1_osp_dir)
        self.resolution = resolution
        self.number_subpixel = number_subpixel
        self._utm_coor: dict[int, tuple[geocal.OgrWrapper, np.ndarray, np.ndarray]] = {}
        self.use_file_cache = False
        self.run_config = run_config
        self.inlist = inlist
        self.collection_label = collection_label
        self.build_id = build_id
        self.pge_version = pge_version
        self.browse_size = browse_size

    def create_standard_metadata(
        self,
        mi: geocal.MapInfo,
        fin_l1cg: h5py.File,
        tile_id: str,
        fout: Path,
        fout2: Path,
    ) -> L1ctWriteStandardMetadata:
        # Right now we use the same metadata as L1CT. This might possibly change in
        # the future
        l1g1 = fin_l1cg["/HDFEOS/ADDITIONAL/FILE_ATTRIBUTES/StandardMetadata"]
        l1g2 = fin_l1cg["/HDFEOS/ADDITIONAL/FILE_ATTRIBUTES/L1CGMetadata"]
        t = l1g2["CalibrationGainCorrection"][:]
        cal_correction = np.empty((2, t.shape[0]))
        cal_correction[0, :] = t
        cal_correction[1, :] = l1g2["CalibrationOffsetCorrection"][:]
        m = L1ctWriteStandardMetadata(
            None,
            xml_file=fout,
            json_file=fout2,
            product_specfic_group="",
            proc_lev_desc="Level 2 Tiled LSTE",
            pge_name="L2C",
            collection_label=self.collection_label,
            build_id=self.build_id,
            pge_version=self.pge_version,
            orbit_corrected=l1g2["OrbitCorrectionPerformed"][()]
            == b"True",
            tcorr_before=l1g2["DeltaTimeOfCorrectionBeforeScene"][()],
            tcorr_after=l1g2["DeltaTimeOfCorrectionAfterScene"][()],
            geolocation_accuracy_qa=l1g2["GeolocationAccuracyQA"][
                ()
            ].decode("utf-8"),
            over_all_land_fraction=l1g2["OverAllLandFraction"][()],
            average_solar_zenith=l1g2["AverageSolarZenith"][()],
            qa_precentage_missing=l1g2["QAPercentMissingData"],
            band_specification=l1g2["BandSpecification"],
            cal_correction=cal_correction,
        )
        m.set("RegionID", tile_id)
        m.set("DataFormatType", "COG")
        m.set("HDFVersionID", None)
        if self.run_config is not None:
            m.process_run_config_metadata(self.run_config)
        m.set("CloudCover", l1g1["CloudCover"][()])
        conv = mi.coordinate_converter
        g1 = conv.convert_from_coordinate(mi.ulc_x, mi.ulc_y)
        g2 = conv.convert_from_coordinate(mi.lrc_x, mi.ulc_y)
        g3 = conv.convert_from_coordinate(mi.lrc_x, mi.lrc_y)
        g4 = conv.convert_from_coordinate(mi.ulc_x, mi.lrc_y)
        m.set(
            "WestBoundingCoordinate",
            np.array([g1.longitude, g2.longitude, g3.longitude, g4.longitude]).min(),
        )
        m.set(
            "EastBoundingCoordinate",
            np.array([g1.longitude, g2.longitude, g3.longitude, g4.longitude]).max(),
        )
        m.set(
            "SouthBoundingCoordinate",
            np.array([g1.latitude, g2.latitude, g3.latitude, g4.latitude]).min(),
        )
        m.set(
            "NorthBoundingCoordinate",
            np.array([g1.latitude, g2.latitude, g3.latitude, g4.latitude]).max(),
        )
        bnd = geocal.ShapeLayer.polygon_2d(
            [
                [g1.latitude, g1.longitude],
                [g2.latitude, g2.longitude],
                [g3.latitude, g3.longitude],
                [g3.latitude, g4.longitude],
            ]
        )
        m.set("SceneBoundaryLatLonWKT", str(bnd))
        m.set("CRS", to_proj4(g1))
        m.set(
            "FieldOfViewObstruction",
            l1g1["FieldOfViewObstruction"][()].decode("utf-8"),
        )
        m.set("ImageLines", mi.number_y_pixel)
        m.set("ImagePixels", mi.number_x_pixel)
        m.set("ImageLineSpacing", self.resolution)
        m.set("ImagePixelSpacing", self.resolution)
        m.set(
            "RangeBeginningDate",
            l1g1["RangeBeginningDate"][()].decode("utf-8"),
        )
        m.set(
            "RangeBeginningTime",
            l1g1["RangeBeginningTime"][()].decode("utf-8"),
        )
        m.set(
            "RangeEndingDate",
            l1g1["RangeEndingDate"][()].decode("utf-8"),
        )
        m.set(
            "RangeEndingTime",
            l1g1["RangeEndingTime"][()].decode("utf-8"),
        )
        m.set(
            "DayNightFlag", l1g1["DayNightFlag"][()].decode("utf-8")
        )
        m.set_input_pointer(self.inlist)
        m.set("SISName", "Level 2 Product Specification Document (JPL D-94635)")
        return m

    def run(self, pool: None | Pool = None) -> None:
        vzen = geocal.GdalRasterImage(
            f'HDF5:"{self.l1cg}"://HDFEOS/GRIDS/ECO_L1CG_RAD_70m/Data_Fields/view_zenith'
        )
        mi = vzen.map_info
        vzen = None
        xindex, yindex = np.meshgrid(
            list(range(mi.number_x_pixel)), list(range(mi.number_y_pixel))
        )
        self.lon, self.lat = mi.index_to_coordinate(xindex, yindex)
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
            self.lat = None
            self.lon = None
            _ = pool.map(self.process_tile, shp_dict_list)

    def utm_coor(self, epsg: int) -> tuple[geocal.OgrWrapper, np.ndarray, np.ndarray]:
        """Calculate utm coordinate. We can optional save/load from disk if needed - this
        is to support multiprocessing"""
        if epsg not in self._utm_coor:
            cache_fname = Path(f"epsg_{epsg}.npy")
            owrap = geocal.OgrWrapper.from_epsg(epsg)
            if self.use_file_cache and cache_fname.exists():
                x, y = np.load(cache_fname, mmap_mode="r")
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
                        np.save(f, [x, y])
                    return (owrap, x, y)
                else:
                    self._utm_coor[epsg] = (owrap, x, y)
        return self._utm_coor[epsg]

    def write_preview(
        self,
        fname: str,
        mi: geocal.MapInfo,
        data: np.ndarray,
        vmin: float | None,
        vmax: float | None,
        din: np.ndarray | None = None,
        vicar_fname: str | None = None,
    ) -> None:
        """Create jpeg preview of the given data. Not sure how useful this actually is,
        but this was done in collection 2 so we want to match that.

        Because it is so related, we optionally take a vicar file name. If this is
        supplied, the data is also saved to this file. This is then used in write_browse."""
        # If vmin and vmax aren't supplied, use a simple algorithm to calculate this
        if(vmax is None or vmin is None):
            # Get the range to use in the jpeg preview. We use the full range
            # of all the data, so we don't have weird changes in the color map from one
            # tile to the next
            if np.count_nonzero(din > fill_value_threshold) > 0:
                mn = din[din > fill_value_threshold].min()
                mx = din[din > fill_value_threshold].max()
                mean = np.mean(din[din > fill_value_threshold])
                sd = np.std(din[din > fill_value_threshold])
                vmin = max(mean - 2 * sd, mn)
                vmax = min(mean + 2 * sd, mx)
            else:
                vmin = 0
                vmax = 1
        if(vmin == vmax):
            vmax += 1.0
        # Scale data from 0.0 to 1.0, which is what the cmap uses
        data_scaled = (data - float(vmin)) / (float(vmax) - float(vmin))
        data_scaled[data_scaled < 0.0] = 0.0
        data_scaled[data_scaled > 1.0] = 1.0
        cmap = plt.get_cmap("jet")
        # Map to rgba, in the range 0.0 to 1.0
        image_array_norm = cmap(data_scaled)
        # Then scale to 0 to 255 as a byte
        image_array_int = (image_array_norm * 255).astype(np.uint8)
        # Write out as jpeg
        ras_r = geocal.GdalRasterImage("", "MEM", mi, 3, geocal.GdalRasterImage.Byte)
        ras_g = gdal_band(ras_r, 2)
        ras_b = gdal_band(ras_r, 3)
        ras_r.write(0, 0, image_array_int[:, :, 0])
        ras_g.write(0, 0, image_array_int[:, :, 1])
        ras_b.write(0, 0, image_array_int[:, :, 2])
        write_gdal(fname, "JPEG", ras_r, "")
        if vicar_fname is not None:
            # Scale to 1 to 255, leaving 0 for nodata
            data_scaled *= 254.9
            data_scaled += 1.0
            data_scaled[np.isnan(data_scaled)] = 0
            # Clip, in case round off takes us past the end
            data_scaled[data_scaled < 0.0] = 0.0
            data_scaled[data_scaled > 255.0] = 255.0
            d = geocal.mmap_file(vicar_fname, mi, nodata=0.0, dtype=np.uint8)
            d[:] = data_scaled.astype(np.uint8)
            d = None

    def write_browse(self, dirname: Path) -> None:
        cmd_merge = [
            "gdal_translate",
            "-of",
            "png",
            "-outsize",
            f"{self.browse_size}",
            f"{self.browse_size}",
            str(dirname / f"{dirname}_LST.jpeg"),
            str(dirname.parent / f"{dirname.name}.png"),
        ]
        subprocess.run(cmd_merge)
        for filename in dirname.parent.glob(f"{dirname.name}.png.*"):
            filename.unlink()

    def process_field(self, field_name, dirname, mi, res, din, dtype=geocal.GdalRasterImage.Float32, use_smallest_ic=False):
        din[np.isnan(din)] = FILL_VALUE_BAD_OR_MISSING
        data_in = MemoryRasterImageFloat(din.shape[0], din.shape[1])
        data_in.write(0, 0, din)
        data = res.resample_field(data_in, 1.0, False, np.nan if dtype == geocal.GdalRasterImage.Float32 else 0, use_smallest_ic)
        f = geocal.GdalRasterImage("", "MEM", mi, 1, dtype)
        if dtype == geocal.GdalRasterImage.Float32:
            set_fill_value(f, np.nan)
        write_data(f, data)
        write_gdal(
            str(dirname / f"{dirname.name}_{field_name}.tif"),
            "COG",
            f,
            "BLOCKSIZE=256 COMPRESS=DEFLATE",
        )
        f.close()
        self.write_preview(
            str(dirname / f"{dirname.name}_{field_name}.jpeg"), mi, data, None, None,
            din=din
        )
        
    def process_tile(self, shp: dict) -> bool:
        logger.info(f"Processing {shp['tile_id']}")
        x: np.ndarray | None = None
        y: np.ndarray | None = None
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
        lstart, lend, sstart, send = Resampler.determine_range(x, y, mi, self.number_subpixel)
        if(lend < lstart or send < sstart):
            logger.info("Tile is empty, skipping")
            logger.info(f"Done with {shp['tile_id']}")
            x = None
            y = None
            return False
        lrange = slice(lstart,(lend+self.number_subpixel))
        srange = slice(sstart,(send+self.number_subpixel))
        res = Resampler(x[lrange,srange], y[lrange,srange], mi, self.number_subpixel, True)
        # Range for data, before we expand to the number of subpixels
        lrange = slice(lstart // self.number_subpixel, lend // self.number_subpixel + 1)
        srange = slice(sstart // self.number_subpixel, send // self.number_subpixel + 1)
        # Free up memory
        x = None
        y = None
        logger.info("Done with Resampler init")
        # Note in general we may get tiles in our search of the shape file that
        # don't actually end up having any data once we look in detail. Just
        # skip tiles that will be empty
        fin_l1cg = h5py.File(self.l1cg, "r")
        din = fin_l1cg["/HDFEOS/GRIDS/ECO_L1CG_RAD_70m/Data Fields/view_zenith"][lrange, srange]
        # Change nan to fill value
        din[np.isnan(din)] = FILL_VALUE_BAD_OR_MISSING
        data_in = MemoryRasterImageFloat(din.shape[0], din.shape[1])
        data_in.write(0, 0, din)
        if res.empty_resample(data_in):
            logger.info("Tile is empty, skipping")
            logger.info(f"Done with {shp['tile_id']}")
            res = None
            fin_l1cg.close()
            din = None
            data_in = None
            return False
        dirname = Path(str(self.output_pattern).replace("TILE", shp["tile_id"]))
        geocal.makedirs_p(dirname)
        m = self.create_standard_metadata(mi, fin_l1cg, shp['tile_id'], dirname.parent / f"{dirname.name}.zip.xml", dirname / f"{dirname.name}.json")
        # view zenith
        logger.info(f"Doing view_zenith - {shp['tile_id']}")
        # data_in read above, we used this for checking for empty tiles.
        data = res.resample_field(data_in, 1.0, False, np.nan, True)
        # COG can only create on copy, so we first create this in memory and
        # then write out.
        f = geocal.GdalRasterImage("", "MEM", mi, 1, geocal.GdalRasterImage.Float32)
        set_fill_value(f, np.nan)
        write_data(f, data)
        write_gdal(
            str(dirname / f"{dirname.name}_view_zenith.tif"),
            "COG",
            f,
            "BLOCKSIZE=256 COMPRESS=DEFLATE",
        )
        f.close()
        self.write_preview(
            str(dirname / f"{dirname.name}_view_zenith.jpeg"), mi, data, None, None,
            din=din
        )

        # height
        logger.info(f"Doing height - {shp['tile_id']}")
        self.process_field("height", dirname, mi, res,
               fin_l1cg["/HDFEOS/GRIDS/ECO_L1CG_RAD_70m/Data Fields/height"][lrange, srange])

        fin_l2cg_lste = h5py.File(self.l2cg_lste, "r")
        # cloud, byte
        logger.info(f"Doing cloud - {shp['tile_id']}")
        self.process_field("cloud", dirname, mi, res,
                           fin_l2cg_lste["/HDFEOS/GRIDS/ECO_L2G_LSTE_70m/Data Fields/cloud_mask"][lrange, srange],
                           dtype=geocal.GdalRasterImage.Byte, use_smallest_ic=True)

        # emiswb, float32
        logger.info(f"Doing EmisWB - {shp['tile_id']}")
        self.process_field("EmisWB", dirname, mi, res,
                           fin_l2cg_lste["/HDFEOS/GRIDS/ECO_L2G_LSTE_70m/Data Fields/EmisWB"][lrange, srange],
                           )

        # LST_err, float32
        logger.info(f"Doing LST_err - {shp['tile_id']}")
        self.process_field("LST_err", dirname, mi, res,
                           fin_l2cg_lste["/HDFEOS/GRIDS/ECO_L2G_LSTE_70m/Data Fields/LST_err"][lrange, srange],
                           )

        # LST, float32
        logger.info(f"Doing LST - {shp['tile_id']}")
        self.process_field("LST", dirname, mi, res,
                           fin_l2cg_lste["/HDFEOS/GRIDS/ECO_L2G_LSTE_70m/Data Fields/LST"][lrange, srange],
                           )

        # QC, uint16
        logger.info(f"Doing QC - {shp['tile_id']}")
        self.process_field("QC", dirname, mi, res,
                           fin_l2cg_lste["/HDFEOS/GRIDS/ECO_L2G_LSTE_70m/Data Fields/QC"][lrange, srange],
                           dtype=geocal.GdalRasterImage.UInt16, use_smallest_ic=True,
                           )

        # water, byte
        logger.info(f"Doing water - {shp['tile_id']}")
        self.process_field("water", dirname, mi, res,
                           fin_l2cg_lste["/HDFEOS/GRIDS/ECO_L2G_LSTE_70m/Data Fields/water_mask"][lrange, srange],
                           dtype=geocal.GdalRasterImage.UInt16, use_smallest_ic=True,
                           )

        # We did radiance 2 just to give a simple thing for us to compare against with
        # our l1ct code. Leave this in case we want to come back to this, but normally
        # don't do this.
        if False:
            b = 2
            logger.info(f"Doing radiance band {b} - {shp['tile_id']}")
            self.process_field(f"radiance_{b}", dirname, mi, res,
            fin_l1cg[f"/HDFEOS/GRIDS/ECO_L1CG_RAD_70m/Data Fields/radiance_{b}"][lrange, srange])

        self.write_browse(dirname)
        m.write()
        fin_l1cg.close()
        fin_l2cg_lste.close()
        din = None
        data_in = None
        data = None
        res = None
        # Create zip file
        with ZipFile(str(dirname.parent / f"{dirname.name}.zip"), "w") as fh:
            for filename in Path(dirname).glob(f"{dirname}*"):
                fh.write(filename)
        shutil.rmtree(dirname)

        logger.info(f"Done with {shp['tile_id']}")
        return True


__all__ = ["L2ctGenerate"]
