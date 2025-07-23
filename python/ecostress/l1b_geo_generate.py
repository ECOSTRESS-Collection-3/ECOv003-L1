from __future__ import annotations
import geocal  # type: ignore
from ecostress_swig import (  # type: ignore
    fill_value_threshold,
    GroundCoordinateArray,
    FILL_VALUE_BAD_OR_MISSING,
)
from .pickle_method import *
import h5py  # type: ignore
from .geo_write_standard_metadata import GeoWriteStandardMetadata
from .misc import time_split
import numpy as np
from loguru import logger
import os
import typing

if typing.TYPE_CHECKING:
    from multiprocessing.pool import Pool
    from .cloud_processing import CloudProcessing
    from .run_config import RunConfig


class L1bGeoGenerate(object):
    """This generate a L1B geo output file from a given ImageGroundConnection."""

    def __init__(
        self,
        igc: geocal.ImageGroundConnection,
        cprocess: CloudProcessing,
        radfname: str | os.PathLike[str],
        lwm: geocal.SrtmLwmData,
        output_name: str | os.PathLike[str],
        inlist: list[str],
        is_day: bool,
        field_of_view_obscured: str = "NO",
        run_config: None | RunConfig = None,
        start_line: int = 0,
        number_line: int = -1,
        local_granule_id: str | None = None,
        collection_label: str = "ECOSTRESS",
        build_id: str = "0.30",
        pge_version: str = "0.30",
        correction_done: bool = True,
        tcorr_before: float = -9999,
        tcorr_after: float = -9999,
        geolocation_accuracy_qa: str = "Poor",
    ) -> None:
        """Create a L1bGeoGenerate with the given ImageGroundConnection
        and output file name. To actually generate, execute the "run"
        command.

        You can pass the run_config in which is used to fill in some of the
        metadata. Without this, we skip that metadata and just have fill data.
        This is useful for testing, but for production you will always want to
        have the run config available."""
        self.igc = igc
        self.gc_arr = GroundCoordinateArray(self.igc, True)
        self.cprocess = cprocess
        self.radfname = radfname
        self.lwm = lwm
        self.is_day = is_day
        self.field_of_view_obscured = field_of_view_obscured
        self.output_name = output_name
        self.start_line = start_line
        self.number_line = number_line
        self.run_config = run_config
        self.local_granule_id = local_granule_id
        self.log = None
        self.collection_label = collection_label
        self.build_id = build_id
        self.pge_version = pge_version
        self.inlist = inlist
        self.correction_done = correction_done
        self.tcorr_before = tcorr_before
        self.tcorr_after = tcorr_after
        self.geolocation_accuracy_qa = geolocation_accuracy_qa

    def loc_parallel_func(
        self, it: tuple[int, int]
    ) -> tuple[
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
    ]:
        """Variation of loc that is easier to use with a multiprocessor pool."""
        start_line, number_line = it
        try:
            # Note res here refers to an internal cache array of gc_arr
            res = self.gc_arr.ground_coor_scan_arr(start_line, number_line)
            logger.info(f"Done with [{start_line}, {start_line + res.shape[0]}]")
        except RuntimeError:
            res = np.empty((number_line, self.igc.image.number_sample, 1, 1, 7))
            res[:] = FILL_VALUE_BAD_OR_MISSING
            logger.info(f"Skipping [{start_line}, {start_line + res.shape[0]}]")
        # Note the copy() here is very important. As an optimization,
        # ground_coor_scan_arr return a reference to an internal cache
        # variable. This array gets overwritten in the next call to
        # ground_coor_scan_arr. So we need to explicitly copy anything
        # we want to keep.
        lat = res[:, :, 0, 0, 0].copy()
        lon = res[:, :, 0, 0, 1].copy()
        height = res[:, :, 0, 0, 2].copy()
        vzenith = res[:, :, 0, 0, 3].copy()
        vazimuth = res[:, :, 0, 0, 4].copy()
        szenith = res[:, :, 0, 0, 5].copy()
        sazimuth = res[:, :, 0, 0, 6].copy()
        # Work around a bug in SrtmDem when we get very close to
        # longitude 180. We should fix this is geocal, but that is
        # pretty involved. So for now, tweak the longitude values so we
        # don't run into this. See git Issue #138
        lon_tweak = lon.copy()
        lon_tweak[lon_tweak > 179] = 179.0
        lfrac = GroundCoordinateArray.interpolate(self.lwm, lat, lon_tweak)
        lfrac = np.where(
            lfrac <= fill_value_threshold, fill_value_threshold, lfrac * 100.0
        )
        tlinestart = np.array(
            [
                self.igc.pixel_time(geocal.ImageCoordinate(ln, 0)).j2000
                for ln in range(start_line, start_line + res.shape[0])
            ]
        )
        return (
            lat,
            lon,
            height,
            vzenith,
            vazimuth,
            szenith,
            sazimuth,
            lfrac,
            tlinestart,
        )

    def loc(
        self, pool: None | Pool = None
    ) -> tuple[
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
    ]:
        """Determine locations"""
        it = []
        for i in range(self.igc.number_scan):
            ls, le = self.igc.scan_index_to_line(i)
            le2 = self.start_line + self.number_line
            if self.start_line < le and (self.number_line == -1 or le2 >= ls):
                if self.number_line == -1:
                    it.append((ls, le - ls))
                else:
                    it.append((ls, min(le - ls, le2 - ls)))
        if pool is None:
            r = list(map(self.loc_parallel_func, it))
        else:
            r = pool.map(self.loc_parallel_func, it)
        lat = np.vstack([rv[0] for rv in r])
        lon = np.vstack([rv[1] for rv in r])
        height = np.vstack([rv[2] for rv in r])
        vzenith = np.vstack([rv[3] for rv in r])
        vazimuth = np.vstack([rv[4] for rv in r])
        szenith = np.vstack([rv[5] for rv in r])
        sazimuth = np.vstack([rv[6] for rv in r])
        lfrac = np.vstack([rv[7] for rv in r])
        tlinestart = np.hstack([rv[8] for rv in r])
        return lat, lon, height, vzenith, vazimuth, szenith, sazimuth, lfrac, tlinestart

    def run(self, pool: None | Pool = None) -> None:
        """Do the actual generation of data."""
        lat, lon, height, vzenith, vazimuth, szenith, sazimuth, lfrac, tlinestart = (
            self.loc(pool)
        )
        rad_band_4 = h5py.File(self.radfname, "r")["//Radiance/radiance_4"][:, :]
        if(hasattr(self.igc, "start_sample")):
            # Subset if we are working with subsetted data
            rad_band_4 = rad_band_4[:,self.igc.start_sample:self.igc.start_sample+self.igc.number_sample]
        cloud, cloudconf = self.cprocess.process_cloud(
            rad_band_4, lat, lon, height, geocal.Time.time_j2000(tlinestart[0])
        )
        self.cloud_cover = (
            np.count_nonzero(cloud == 1) / np.count_nonzero(cloud != 255)
        ) * 100.0
        fout = h5py.File(self.output_name, "w")
        m = GeoWriteStandardMetadata(
            fout,
            product_specfic_group="L1GEOMetadata",
            proc_lev_desc="Level 1B Geolocation Parameters",
            pge_name="L1B_GEO",
            collection_label=self.collection_label,
            build_id=self.build_id,
            pge_version=self.pge_version,
            orbit_corrected=self.correction_done,
            tcorr_before=self.tcorr_before,
            tcorr_after=self.tcorr_after,
            geolocation_accuracy_qa=self.geolocation_accuracy_qa,
            local_granule_id=self.local_granule_id,
        )
        if self.run_config is not None:
            m.process_run_config_metadata(self.run_config)
        if(hasattr(self.igc, "time_table")):
            tt = self.igc.time_table
        else:
            tt = self.igc.sub_time_table
        m.set("CloudCover", self.cloud_cover)
        m.set("WestBoundingCoordinate", lon[lon > -998].min())
        m.set("EastBoundingCoordinate", lon[lon > -998].max())
        m.set("SouthBoundingCoordinate", lat[lat > -998].min())
        m.set("NorthBoundingCoordinate", lat[lat > -998].max())
        m.set("FieldOfViewObstruction", self.field_of_view_obscured)
        m.set("ImageLines", lat.shape[0])
        m.set("ImagePixels", lat.shape[1])
        dt, tm = time_split(tt.min_time)
        m.set("RangeBeginningDate", dt)
        m.set("RangeBeginningTime", tm)
        dt, tm = time_split(tt.max_time)
        m.set("RangeEndingDate", dt)
        m.set("RangeEndingTime", tm)
        m.set("DayNightFlag", "Day" if self.is_day else "Night")
        m.set_input_pointer(self.inlist)
        g = fout.create_group("Geolocation")
        g.attrs["Projection"] = """\
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
"""
        g.attrs["Projection_WKT"] = """\
GEOGCS["WGS 84",
    DATUM["WGS_1984",
        SPHEROID["WGS 84",6378137,298.257223563,
            AUTHORITY["EPSG","7030"]],
        AUTHORITY["EPSG","6326"]],
    PRIMEM["Greenwich",0],
    UNIT["degree",0.0174532925199433],
    AUTHORITY["EPSG","4326"]]
"""
        t = g.create_dataset("latitude", data=lat, dtype="f8", compression="gzip")
        t.attrs["Units"] = "degrees"
        t.attrs["valid_min"] = -90
        t.attrs["valid_max"] = 90
        t = g.create_dataset("longitude", data=lon, dtype="f8", compression="gzip")
        t.attrs["Units"] = "degrees"
        t.attrs["valid_min"] = -180
        t.attrs["valid_max"] = 180
        t = g.create_dataset("height", data=height, dtype="f4", compression="gzip")
        t.attrs["Units"] = "m"
        t = g.create_dataset(
            "land_fraction", data=lfrac, dtype="f4", compression="gzip"
        )
        t.attrs["Units"] = "percentage"
        t.attrs["valid_min"] = 0
        t.attrs["valid_max"] = 100
        t.attrs["fill"] = -9999
        t = g.create_dataset(
            "view_zenith", data=vzenith, dtype="f4", compression="gzip"
        )
        t.attrs["Units"] = "degrees"
        t.attrs["valid_min"] = -90
        t.attrs["valid_max"] = 90
        t = g.create_dataset(
            "view_azimuth", data=vazimuth, dtype="f4", compression="gzip"
        )
        t.attrs["Units"] = "degrees"
        t.attrs["valid_min"] = -180
        t.attrs["valid_max"] = 180
        t = g.create_dataset(
            "solar_zenith", data=szenith, dtype="f4", compression="gzip"
        )
        t.attrs["Units"] = "degrees"
        t.attrs["valid_min"] = -90
        t.attrs["valid_max"] = 90
        t = g.create_dataset(
            "solar_azimuth", data=sazimuth, dtype="f4", compression="gzip"
        )
        t.attrs["Units"] = "degrees"
        t.attrs["valid_min"] = -180
        t.attrs["valid_max"] = 180
        t = g.create_dataset(
            "prelim_cloud_mask", data=cloud, dtype="u1", compression="gzip"
        )
        t.attrs["Units"] = "dimensionless"
        t.attrs["valid_min"] = 0
        t.attrs["valid_max"] = 0
        t.attrs["fill"] = 255
        t.attrs["Description"] = (
            "This is the preliminary cloud mask. O for clear, 1 for cloudy, 255 for pixels we can't calculate cloud mask for"
        )
        t = g.create_dataset("line_start_time_j2000", data=tlinestart, dtype="f8")
        t.attrs["Description"] = "J2000 time of first pixel in line"
        t.attrs["Units"] = "second"
        m.write()
        g = fout[m.product_specfic_group]
        avg_sz = szenith[szenith > fill_value_threshold].mean()
        oa_lf = lfrac[lfrac > fill_value_threshold].mean()
        d = g.create_dataset("AverageSolarZenith", data=avg_sz)
        d.attrs["Units"] = "degrees"
        d.attrs["valid_min"] = -90
        d.attrs["valid_max"] = 90
        d.attrs["Description"] = "Average solar zenith angle for scene"
        d = g.create_dataset("OverAllLandFraction", data=oa_lf)
        d.attrs["Units"] = "percentage"
        d.attrs["valid_min"] = 0
        d.attrs["valid_max"] = 100
        d.attrs["Description"] = "Overall land fraction for scene"
        # We stash some of the objects we've used here for use by
        # L1bGeoGenerateMap and L1bGeoGenerateKmz. Right now, we assume
        # this is always run first. We could break this dependency if
        # needed, but at least currently we always run L1bGeoGenerate and
        # sometimes run L1bGeoGenerateMap and L1bGeoGenerateKmz
        m.hdf_file = None
        self.m = m
        self.lat = lat
        self.lon = lon
        self.avg_sz = avg_sz
        self.oa_lf = oa_lf


__all__ = ["L1bGeoGenerate"]
