from __future__ import annotations
import geocal  # type: ignore
from ecostress_swig import (  # type: ignore
    fill_value_threshold,
    Resampler,
    HdfEosFileHandle,
    HdfEosGrid,
    GroundCoordinateArray,
)
from .l1cg_write_standard_metadata import L1cgWriteStandardMetadata
from .gaussian_stretch import gaussian_stretch
import subprocess
import h5py  # type: ignore
import scipy  # type: ignore
import numpy as np
from loguru import logger
from pathlib import Path
import os
import typing

if typing.TYPE_CHECKING:
    from .run_config import RunConfig


class L1cgGenerate:
    """The L1CG product is HDFEOS5. This isn't something I would have necessarily
    picked, HDFEOS5 really was never used very widely. But this was put in for
    collection 2, and we want to support the format.

    We can mostly generate this using the standard h5py library. While there is
    a HDFEOS5 library (with limited support in our swig/C++ code) it is actually
    easier just to use h5py. HDFEOS is a HDF5 file with some conventions, see
    the document https://www.earthdata.nasa.gov/s3fs-public/imported/ESDS-RFC-008-v1.1.pdf
    for a description of this. Primarily we need a specific (simple) convention about
    where to put grids, fields in those grid, and various metadata. Also, we
    generate a StructMetadata.0. This has information in a format called "ODL".
    We use the C++/SWIG to generate a initial HDFEOS file, and then just reopen this
    with h5py to populate this.

    Note that newer versions of GDAL can read the projection/map information from
    HDFEOS5 files.
    """

    def __init__(
        self,
        l1b_geo: str | os.PathLike[str],
        l1b_rad: str | os.PathLike[str],
        dem: geocal.Dem,
        lwm: geocal.SrtmLwmData,
        output_name: str | os.PathLike[str],
        inlist: list[str],
        local_granule_id: str | None = None,
        resolution: float = 70,
        number_subpixel: int = 3,
        run_config: RunConfig | None = None,
        collection_label: str = "ECOSTRESS",
        build_id: str = "0.30",
        pge_version: str = "0.30",
        browse_band_list_5band: list[int] = [4, 3, 1],
        browse_band_list_3band: list[int] = [5, 4, 2],
        browse_size: int = 1080,
    ) -> None:
        self.l1b_geo = l1b_geo
        self.l1b_rad = l1b_rad
        self.output_name = Path(output_name)
        if local_granule_id:
            self.local_granule_id = local_granule_id
        else:
            self.local_granule_id = self.output_name.name
        self.dem = dem
        self.lwm = lwm
        self.resolution = resolution
        self.number_subpixel = number_subpixel
        self.run_config = run_config
        self.inlist = inlist
        self.collection_label = collection_label
        self.build_id = build_id
        self.pge_version = pge_version
        fin_rad = h5py.File(self.l1b_rad, "r")
        if "BandSpecification" in fin_rad["L1B_RADMetadata"]:
            nband = np.count_nonzero(
                fin_rad["L1B_RADMetadata/BandSpecification"][:] > 0
            )
        else:
            nband = 6
        self.browse_band_list = (
            browse_band_list_3band if nband == 3 else browse_band_list_5band
        )
        self.browse_size = browse_size

    def create_standard_metadata(
        self,
        mi: geocal.MapInfo,
        fin_rad: h5py.File,
        fin_geo: h5py.File,
        fout: h5py.File,
    ) -> L1cgWriteStandardMetadata:
        t = fin_rad["L1B_RADMetadata/CalibrationGainCorrection"][:]
        cal_correction = np.empty((2, t.shape[0]))
        cal_correction[0, :] = t
        cal_correction[1, :] = fin_rad["L1B_RADMetadata/CalibrationOffsetCorrection"][:]
        m = L1cgWriteStandardMetadata(
            fout,
            product_specfic_group="L1CGMetadata",
            proc_lev_desc="Level 1C Gridded Parameters",
            pge_name="L1C",
            collection_label=self.collection_label,
            build_id=self.build_id,
            pge_version=self.pge_version,
            orbit_corrected=fin_geo["L1GEOMetadata/OrbitCorrectionPerformed"][()]
            == b"True",
            tcorr_before=fin_geo["L1GEOMetadata/DeltaTimeOfCorrectionBeforeScene"][()],
            tcorr_after=fin_geo["L1GEOMetadata/DeltaTimeOfCorrectionAfterScene"][()],
            geolocation_accuracy_qa=fin_geo["L1GEOMetadata/GeolocationAccuracyQA"][
                ()
            ].decode("utf-8"),
            over_all_land_fraction=fin_geo["L1GEOMetadata/OverAllLandFraction"][()],
            average_solar_zenith=fin_geo["L1GEOMetadata/AverageSolarZenith"][()],
            qa_precentage_missing=fin_rad["L1B_RADMetadata/QAPercentMissingData"],
            band_specification=fin_rad["L1B_RADMetadata/BandSpecification"],
            cal_correction=cal_correction,
            local_granule_id=self.local_granule_id,
        )
        if self.run_config is not None:
            m.process_run_config_metadata(self.run_config)
        m.set("CloudCover", fin_geo["StandardMetadata/CloudCover"][()])
        m.set("WestBoundingCoordinate", mi.ulc_x)
        m.set("EastBoundingCoordinate", mi.lrc_x)
        m.set("SouthBoundingCoordinate", mi.lrc_y)
        m.set("NorthBoundingCoordinate", mi.ulc_y)
        m.set(
            "FieldOfViewObstruction",
            fin_geo["StandardMetadata/FieldOfViewObstruction"][()],
        )
        m.set("ImageLines", mi.number_y_pixel)
        m.set("ImagePixels", mi.number_x_pixel)
        m.set("ImageLineSpacing", self.resolution)
        m.set("ImagePixelSpacing", self.resolution)
        m.set("RangeBeginningDate", fin_geo["StandardMetadata/RangeBeginningDate"][()])
        m.set("RangeBeginningTime", fin_geo["StandardMetadata/RangeBeginningTime"][()])
        m.set("RangeEndingDate", fin_geo["StandardMetadata/RangeEndingDate"][()])
        m.set("RangeEndingTime", fin_geo["StandardMetadata/RangeEndingTime"][()])
        m.set("DayNightFlag", fin_geo["StandardMetadata/DayNightFlag"][()])
        m.set_input_pointer(self.inlist)
        bnd = geocal.ShapeLayer.polygon_2d([[mi.ulc_x,  mi.ulc_y], [mi.ulc_x, mi.lrc_y],
                                            [mi.lrc_x, mi.lrc_y], [mi.lrc_x, mi.ulc_y]])
        m.set("SceneBoundaryLatLonWKT", str(bnd))
        return m

    def save_for_browse(self, mi: geocal.MapInfo, data: np.ndarray, b: int) -> None:
        """If this band is part of the browse product, create an intermediate file that
        then gets used in write_browse"""
        # Create data for browse product
        if b in self.browse_band_list:
            data = data.copy()
            data[np.isnan(data)] = -999.0
            data_scaled = gaussian_stretch(data)
            fname = str(
                self.output_name.parent / f"{self.output_name.stem}_b{b}_scaled.img"
            )
            d = geocal.mmap_file(fname, mi, nodata=0.0, dtype=np.uint8)
            d[:] = data_scaled
            d = None

    def write_browse(self, mi: geocal.MapInfo) -> None:
        """Write out the browse product"""
        cmd_merge = [
            "gdalbuildvrt",
            "-q",
            "-separate",
            str(self.output_name.parent / f"{self.output_name.stem}_scaled.vrt"),
        ]
        for b in self.browse_band_list:
            cmd_merge.append(
                str(
                    self.output_name.parent / f"{self.output_name.stem}_b{b}_scaled.img"
                )
            )
        subprocess.run(cmd_merge)
        # Size of 0 tells GDAL to maintain the aspect ratio
        if mi.number_x_pixel > mi.number_y_pixel:
            xsize = self.browse_size
            ysize = 0
        else:
            xsize = 0
            ysize = self.browse_size
        cmd_merge = [
            "gdal_translate",
            "-of",
            "png",
            "-outsize",
            f"{xsize}",
            f"{ysize}",
            str(self.output_name.parent / f"{self.output_name.stem}_scaled.vrt"),
            str(self.output_name.parent / f"{self.output_name.stem}.png"),
        ]
        subprocess.run(cmd_merge)
        for filename in self.output_name.parent.glob(f"{self.output_name.stem}.png.*"):
            filename.unlink()

    def run(self) -> None:
        mi = geocal.cib01_mapinfo(self.resolution)
        fin_geo = h5py.File(self.l1b_geo, "r")
        fin_rad = h5py.File(self.l1b_rad, "r")
        latv = fin_geo["Geolocation/latitude"][:, :]
        lonv = fin_geo["Geolocation/longitude"][:, :]
        # Make sure fill values are negative enough that is clear we
        # should ignore them, even after interpolation
        latv[latv < fill_value_threshold] = -1e20
        lonv[lonv < fill_value_threshold] = -1e20
        # Order 1 is bilinear interpolation
        lat = scipy.ndimage.interpolation.zoom(latv, self.number_subpixel, order=1)
        lon = scipy.ndimage.interpolation.zoom(lonv, self.number_subpixel, order=1)
        res = Resampler(lon, lat, mi, self.number_subpixel, False)
        logger.info("Done with Resampler init")
        mi = res.map_info
        # Create HDFEOS file. We just create the structure here. Note it
        # looks like we are creating a bunch of fields and then deleting them.
        # But this is actually efficient, we have compression turned on and these
        # fields are size 0. So we just create placeholders here, and then fill
        # them in the next step.
        fout = HdfEosFileHandle(str(self.output_name), HdfEosFileHandle.TRUNC)
        g = HdfEosGrid(fout, "ECO_L1CG_RAD_70m", mi)
        g.add_field_uchar("prelim_cloud_mask")
        g.add_field_uchar("water")
        g.add_field_float("view_zenith")
        g.add_field_float("height")
        for i in range(5):
            g.add_field_float(f"data_quality_{i + 1}")
            g.add_field_float(f"radiance_{i + 1}")
            g.add_field_float(f"interpolation_uncertainty_{i + 1}")
        g.close()
        fout.close()
        fout = h5py.File(self.output_name, "r+")
        dfield = fout["//HDFEOS/GRIDS/ECO_L1CG_RAD_70m/Data Fields"]
        del dfield["prelim_cloud_mask"]
        del dfield["water"]
        del dfield["view_zenith"]
        del dfield["height"]
        for i in range(5):
            del dfield[f"data_quality_{i + 1}"]
            del dfield[f"radiance_{i + 1}"]
            del dfield[f"interpolation_uncertainty_{i + 1}"]

        m = self.create_standard_metadata(mi, fin_rad, fin_geo, fout)
        # Not sure if having this open interferes with GDAL, but simple enough to close
        fin_rad = None
        for b in range(1, 6):
            logger.info("Doing radiance band %d" % b)
            data_in = geocal.GdalRasterImage(
                f'HDF5:"{self.l1b_rad}"://Radiance/radiance_{b}'
            )
            data = res.resample_field(data_in, 1.0, False, np.nan).astype(np.float32)
            t = dfield.create_dataset(
                "radiance_%d" % b,
                data=data,
                dtype="f4",
                fillvalue=np.nan,
                compression="gzip",
            )
            t.attrs.create("_FillValue", data=np.nan, dtype=t.dtype)
            t.attrs["Units"] = "W/m^2/sr/um"
            self.save_for_browse(mi, data, b)
        self.write_browse(mi)
        for b in range(1, 6):
            logger.info("Doing uncertainty band %d" % b)
            data_in = geocal.GdalRasterImage(
                f'HDF5:"{self.l1b_rad}"://Radiance/interpolation_uncertainty_{b}'
            )
            data = res.resample_field(data_in, 1.0, False, np.nan).astype(np.float32)
            t = dfield.create_dataset(
                "interpolation_uncertainty_%d" % b,
                data=data,
                dtype="f4",
                fillvalue=np.nan,
                compression="gzip",
            )
            t.attrs.create("_FillValue", data=np.nan, dtype=t.dtype)
            t.attrs["Units"] = "W/m^2/sr/um"
            t.attrs["Description"] = """
Uncertainty in the interpolated value for data that
we interpolated (so data_quality has value DQI_INTERPOLATED).

See ATB for details.
            
Set to 0.0 for values that we haven't interpolated.
"""
        for b in range(1, 6):
            # GeoCal doesn't support the dqi type. We could update geocal,
            # but no strong reason to. Just read into memory. Probably should have
            # had dqi be uint8 rather than int8, but not worth changing now.
            logger.info("Doing DQI band %d" % b)
            din = h5py.File(self.l1b_rad)[f"Radiance/data_quality_{b}"][:, :]
            data_in = geocal.MemoryRasterImage(din.shape[0], din.shape[1])
            data_in.write(0, 0, din)
            data = res.resample_dqi(data_in).astype(np.uint8)
            t = dfield.create_dataset(
                "data_quality_%d" % b,
                data=data,
                dtype=np.uint8,
                compression="gzip",
            )
            t.attrs["valid_min"] = 0
            t.attrs["valid_max"] = 4
            t.attrs["Description"] = """
Data quality indicator. 
  0 - DQI_GOOD, normal data, nothing wrong with it
  1 - DQI_INTERPOLATED, data was part of instrument 
      'stripe', and we have filled this in with 
      interpolated data (see ATB) 
  2 - DQI_STRIPE_NOT_INTERPOLATED, data was part of
      instrument 'stripe' and we could not fill in
      with interpolated data.
  3 - DQI_BAD_OR_MISSING, indicates data with a bad 
      value (e.g., negative DN) or missing packets.
  4 - DQI_NOT_SEEN, pixels where because of the 
      difference in time that a sample is seen with 
      each band, the ISS has moved enough we haven't 
      seen the pixel. So data is missing, but by
      instrument design instead of some problem. Also
      used for grid pixels that are just outside the range
      seen by ECOSTRESS
"""
            t.attrs["Units"] = "dimensionless"

        logger.info("Doing view_zenith")
        data_in = geocal.GdalRasterImage(
            f'HDF5:"{self.l1b_geo}"://Geolocation/view_zenith'
        )
        data = res.resample_field(data_in, 1.0, False, np.nan, True).astype(np.float32)
        t = dfield.create_dataset(
            "view_zenith",
            data=data,
            dtype="f4",
            fillvalue=np.nan,
            compression="gzip",
        )
        t.attrs.create("_FillValue", data=np.nan, dtype=t.dtype)
        t.attrs["Units"] = "degrees"
        t.attrs["valid_min"] = -90
        t.attrs["valid_max"] = 90
        logger.info("Doing height")
        lat, lon, height = res.map_values(self.dem)
        t = dfield.create_dataset("height", data=height, dtype="f4", compression="gzip")
        t.attrs["Units"] = "m"

        logger.info("Doing water")
        # Work around a bug in SrtmDem when we get very close to
        # longitude 180. We should fix this is geocal, but that is
        # pretty involved. So for now, tweak the longitude values so we
        # don't run into this. See git Issue #138
        lon_tweak = lon.copy()
        lon_tweak[lon_tweak > 179] = 179.0
        lfrac = GroundCoordinateArray.interpolate(self.lwm, lat, lon_tweak)
        # Fill value is 0, so we treat as land 100%
        lfrac = np.where(lfrac <= fill_value_threshold, 100.0, lfrac * 100.0)
        # Water mask is 0 for land or fill, 1 for water. We just threshold of the land fraction
        water_data = np.where(lfrac < 50, 1, 0).astype(np.uint8)
        t = dfield.create_dataset(
            "water",
            data=water_data,
            dtype=np.uint8,
            compression="gzip",
        )
        t.attrs["Description"] = "1 for water, 0 for land or fill value"
        t.attrs["Units"] = "dimensionless"

        logger.info("Doing prelim_cloud_mask")
        din = h5py.File(self.l1b_geo)["Geolocation/prelim_cloud_mask"][:, :]
        # Remove fill value, treat as clear
        din[din > 1] = 0
        data_in = geocal.MemoryRasterImage(din.shape[0], din.shape[1])
        data_in.write(0, 0, din)
        data = res.resample_field(data_in, 1.0, False, 0)
        data = np.where(data < 0.5, 0, 1).astype(np.uint8)
        t = dfield.create_dataset(
            "prelim_cloud_mask",
            data=data,
            dtype=np.uint8,
            compression="gzip",
        )
        t.attrs["Description"] = "1 for cloudy, 0 for clear or fill"
        t.attrs["Units"] = "dimensionless"

        m.write()


__all__ = ["L1cgGenerate"]
