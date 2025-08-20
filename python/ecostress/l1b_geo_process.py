from __future__ import annotations
from .run_config import RunConfig
from .misc import (
    create_orbit_raw,
    create_dem,
    create_lwm,
    ortho_base_directory,
    band_to_landsat_band,
    orbit_from_metadata,
    ecostress_file_name
)
from .l1b_geo_qa_file import L1bGeoQaFile
import geocal  # type: ignore
from ecostress_swig import (  # type: ignore
    EcostressOrbit,
    EcostressOrbitL0Fix,
)
from pathlib import Path
from loguru import logger
from functools import cached_property
import sys
import os
import types
import typing

if typing.TYPE_CHECKING:
    pass


class L1bGeoProcess:
    """Top level process for l1b_geo_process.

    Note that this is really just procedural process - do this, then do that sort of code.
    We use to have this just as a long script in l1b_geo_process, but it got to the point
    that breaking this up and having this in the python library made sense."""

    def __init__(
        self,
        run_config: Path | None = None,
        prod_dir: Path | None = None,
        l1a_raw_att: Path | None = None,
        l1_osp_dir: Path | None = None,
        l1b_rad: list[Path] | None = None,
        ecostress_band: int = -1,
        landsat_band: int = -1,
        number_cpu: int = 10,
        number_line: int = -1,
        # If supplied, should be yaw, pitch, roll to add in degrees
        orbit_offset: list[float] | None = None,
    ):
        if run_config is not None:
            self.process_run_config(run_config)
        else:
            if (
                prod_dir is None
                or l1a_raw_att is None
                or l1_osp_dir is None
                or l1b_rad is None
            ):
                raise RuntimeError(
                    "Need to supply either run_config or prod_dir, l1a_raw_att, l1_osp_dir and l1b_rad"
                )
            self.process_args(prod_dir, l1a_raw_att, l1_osp_dir, l1b_rad, number_cpu)
        self.setup_orthobase(landsat_band, ecostress_band)
        if orbit_offset is not None:
            self.setup_orbit_offset(orbit_offset)
        self.orb : geocal.Orbit = geocal.OrbitOffsetCorrection(self.orb)
        self.cam = geocal.read_shelve(str(self.l1_osp_dir / "camera.xml"))
        # Don't fit any of the camera parameters, hold them all fixed
        self.cam.mask_all_parameter()
        # Update focal length. We may put this into the camera.xml file, but for now
        # we track this separately.
        self.cam.focal_length = self.l1b_geo_config.camera_focal_length
        # Reorder radlist by acquisition_time, it isn't necessarily given to us
        # in order.
        self.radlist: list[Path] = sorted(self.radlist, key=lambda f: orbit_from_metadata(f)[2])
        orbit, scene, acquisition_time = orbit_from_metadata(self.radlist[0])
        self.ofile = ecostress_file_name(
            "L1B_GEO",
            orbit,
            scene,
            acquisition_time,
            build=self.build_id,
            collection_label=self.collection_label,
            version=self.file_version,
        )
        self.qa_file : None | L1bGeoQaFile = None
            

    def setup_orthobase(self, landsat_band: int, ecostress_band: int) -> None:
        """Setup self.ortho_base_night and self.ortho_base_day"""
        if landsat_band == -1:
            lband_day = self.l1b_geo_config.landsat_day_band
            lband_night = self.l1b_geo_config.landsat_night_band
        else:
            lband_day = landsat_band
            lband_night = lband_day
        if ecostress_band == -1:
            self.eband_day = self.l1b_geo_config.ecostress_day_band
            self.eband_night = self.l1b_geo_config.ecostress_night_band
        else:
            self.eband_day = ecostress_band
            self.eband_night = self.eband_day
        self.ortho_base_day = geocal.Landsat7Global(
            str(self.ortho_base_dir), band_to_landsat_band(lband_day)
        )
        self.ortho_base_night = geocal.Landsat7Global(
            str(self.ortho_base_dir), band_to_landsat_band(lband_night)
        )

    def setup_orbit_offset(self, orbit_offset: list[float]) -> None:
        """For testing purposes, can add a known offset to the orbit data."""
        logger.info("Add in orbit errors %s" % orbit_offset)
        # Want this in arcseconds, because this is what OrbitOffsetCorrection
        # takes
        yaw, pitch, roll = [float(i) * 60 * 60 for i in orbit_offset]
        self.orb = geocal.OrbitOffsetCorrection(self.orb)
        self.orb.insert_attitude_time_point(self.orb.min_time)
        self.orb.insert_attitude_time_point(self.orb.max_time)
        self.orb.parameter = [yaw, pitch, roll] * 2
        self.orb.fit_position_x = False
        self.orb.fit_position_y = False
        self.orb.fit_position_z = False
        self.orb.fit_yaw = False
        self.orb.fit_pitch = False
        self.orb.fit_roll = False

    @cached_property
    def l1b_geo_config(self) -> types.ModuleType:
        try:
            sys.path.append(str(self.l1_osp_dir))
            import l1b_geo_config  # type: ignore

            return l1b_geo_config
        finally:
            sys.path.remove(str(self.l1_osp_dir))

    def read_version(self) -> None:
        try:
            sys.path.append(os.environ["ECOSTRESSTOP"])
            from ecostress_version import pge_version, build_id, collection_label  # type: ignore

            self.pge_version = pge_version
            self.build_id = build_id
            self.collection_label = collection_label
        finally:
            sys.path.remove(os.environ["ECOSTRESSTOP"])

    def process_run_config(self, run_config: Path) -> None:
        """Set up things using run config, if supplied"""
        config = RunConfig(run_config)
        self.l1_osp_dir = Path(
            config.as_list("StaticAncillaryFileGroup", "L1_OSP_DIR")[0]
        ).absolute()
        self.ncpu = int(config.as_list("Process", "NumberCpu")[0])
        fix_l0_time_tag = False
        if (
            hasattr(self.l1b_geo_config, "fix_l0_time_tag")
            and self.l1b_geo_config.fix_l0_time_tag
        ):
            fix_l0_time_tag = True
        self.orb = create_orbit_raw(
            config,
            pos_off=self.l1b_geo_config.x_offset_iss,
            extrapolation_pad=self.l1b_geo_config.extrapolation_pad,
            large_gap=self.l1b_geo_config.large_gap,
            fix_l0_time_tag=fix_l0_time_tag,
        )
        self.dem = create_dem(config)
        self.lwm = create_lwm(config)
        self.ortho_base_dir: Path = ortho_base_directory(config)
        self.radlist = [
            Path(i).absolute() for i in config.as_list("InputFileGroup", "L1B_RAD")
        ]
        self.prod_dir = Path(
            config.as_list("ProductPathGroup", "ProductPath")[0]
        ).absolute()
        self.file_version = config.as_list("ProductPathGroup", "ProductCounter")[0]
        self.build_id = config.as_list("PrimaryExecutable", "BuildID")[0]
        self.collection_label = config.as_list("ProductPathGroup", "CollectionLabel")[0]
        self.orbfname = Path(
            config.as_list("TimeBasedFileGroup", "L1A_RAW_ATT")[0]
        ).absolute()

    def process_args(
        self,
        prod_dir: Path,
        l1a_raw_att: Path,
        l1_osp_dir: Path,
        l1b_rad: list[Path],
        number_cpu: int,
    ) -> None:
        """Set up things using command line arguments, if supplied"""
        self.l1_osp_dir = l1_osp_dir.absolute()
        self.ncpu = number_cpu
        self.file_version = "01"
        fix_l0_time_tag = False
        if (
            hasattr(self.l1b_geo_config, "fix_l0_time_tag")
            and self.l1b_geo_config.fix_l0_time_tag
        ):
            fix_l0_time_tag = True
        self.orbfname = l1a_raw_att.absolute()
        if fix_l0_time_tag:
            self.orb = EcostressOrbitL0Fix(
                str(self.orbfname),
                self.l1b_geo_config.x_offset_iss,
                self.l1b_geo_config.extrapolation_pad,
                self.l1b_geo_config.large_gap,
            )
        else:
            self.orb = EcostressOrbit(
                str(self.orbfname),
                self.l1b_geo_config.x_offset_iss,
                self.l1b_geo_config.extrapolation_pad,
                self.l1b_geo_config.large_gap,
            )
        self.dem = geocal.SrtmDem(
            os.environ["ELEV_ROOT"],
            False,
            geocal.DatumGeoid96(os.environ["AFIDS_VDEV_DATA"] + "/EGM96_20_x100.HLF"),
        )
        if Path("/raid25/SRTM_2014_update/srtm_v3_lwm").exists():
            self.lwm = geocal.SrtmLwmData("/raid25/SRTM_2014_update/srtm_v3_lwm", False)
        elif Path("/project/ancillary/SRTM/srtm_v3_lwm").exists():
            self.lwm = geocal.SrtmLwmData("/project/ancillary/SRTM/srtm_v3_lwm", False)
        else:
            raise RuntimeError("Can't find land/water mask data")
        if Path("/raid22/band5_VICAR").exists():
            self.ortho_base_dir = Path("/raid22")
        elif Path("/data/smyth/Landsat/band5_VICAR").exists():
            self.ortho_base_dir = Path("/data/smyth/Landsat")
        elif Path("/project/ancillary/LANDSAT").exists():
            self.ortho_base_dir = Path("/project/ancillary/LANDSAT")
        else:
            raise RuntimeError("Can't find Landsat global orthobase data")
        self.radlist = [Path(i).absolute() for i in l1b_rad]
        self.read_version()

    def run(self) -> None:
        """Run the L1bGeoProcess"""
        pass
