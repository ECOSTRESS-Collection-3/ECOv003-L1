from __future__ import annotations
from .run_config import RunConfig
from .misc import (
    create_orbit_raw,
    create_dem,
    create_lwm,
    create_time_table,
    create_scan_mirror,
    ortho_base_directory,
    band_to_landsat_band,
    orbit_from_metadata,
    ecostress_file_name,
    as_string,
    process_run,
)
from .l1b_geo_qa_file import L1bGeoQaFile
from .cloud_processing import CloudProcessing
from .l1b_geo_generate import L1bGeoGenerate
from .l1b_geo_generate_map import L1bGeoGenerateMap
from .l1b_geo_generate_kmz import L1bGeoGenerateKmz
from .l1b_att_generate import L1bAttGenerate
from .l1b_tp_collect import L1bTpCollect
import geocal  # type: ignore
from ecostress_swig import (  # type: ignore
    EcostressOrbit,
    EcostressOrbitOffsetCorrection,
    EcostressOrbitL0Fix,
    EcostressImageGroundConnection,
    EcostressImageGroundConnectionSubset,
    EcostressIgcCollection,
)
from pathlib import Path
from loguru import logger
from multiprocessing.pool import Pool
from functools import cached_property
import math
import h5py  # type: ignore
import numpy as np
import sys
import os
import io
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
        force_night: bool = False,
        skip_sba: bool = False,
        igccol_use: Path | None = None,
        tpcol_use: Path | None = None,
    ):
        self._line_order_reversed: bool | None = None
        self.force_night = force_night
        self.correction_done = False
        self.number_line = number_line
        self.skip_sba = skip_sba
        self.config: None | RunConfig = None
        self.igccol_use = igccol_use.absolute() if igccol_use is not None else None
        self.tpcol_use = tpcol_use.absolute() if tpcol_use is not None else None
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
        self.orb: geocal.Orbit = EcostressOrbitOffsetCorrection(self.orb)
        self.cam = geocal.read_shelve(str(self.l1_osp_dir / "camera.xml"))
        # Don't fit any of the camera parameters, hold them all fixed
        self.cam.mask_all_parameter()
        # Update focal length. We may put this into the camera.xml file, but for now
        # we track this separately.
        self.cam.focal_length = self.l1b_geo_config.camera_focal_length
        # Reorder radlist by acquisition_time, it isn't necessarily given to us
        # in order.
        self.radlist: list[Path] = sorted(
            self.radlist, key=lambda f: orbit_from_metadata(f)[2]
        )
        orbit, scene, acquisition_time = orbit_from_metadata(self.radlist[0])
        self.log_file = Path(
            ecostress_file_name(
                "L1B_GEO",
                orbit,
                scene,
                acquisition_time,
                build=self.build_id,
                collection_label=self.collection_label,
                version=self.file_version,
            )
        )
        self.log_file = self.prod_dir / (self.log_file.stem + ".log")
        self.log_file = self.log_file.absolute()
        self.qa_file: None | L1bGeoQaFile = None

    def setup_orthobase(self, landsat_band: int, ecostress_band: int) -> None:
        """Setup self.ortho_base_night and self.ortho_base_day"""
        if landsat_band == -1:
            self.lband_day = self.l1b_geo_config.landsat_day_band
            self.lband_night = self.l1b_geo_config.landsat_night_band
        else:
            self.lband_day = landsat_band
            self.lband_night = self.lband_day
        if ecostress_band == -1:
            self.eband_day = self.l1b_geo_config.ecostress_day_band
            self.eband_night = self.l1b_geo_config.ecostress_night_band
        else:
            self.eband_day = ecostress_band
            self.eband_night = self.eband_day
        self.ortho_base_day = geocal.Landsat7Global(
            str(self.ortho_base_dir), band_to_landsat_band(self.lband_day)
        )
        self.ortho_base_night = geocal.Landsat7Global(
            str(self.ortho_base_dir), band_to_landsat_band(self.lband_night)
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
        self.config = RunConfig(run_config)
        self.l1_osp_dir = Path(
            self.config.as_list("StaticAncillaryFileGroup", "L1_OSP_DIR")[0]
        ).absolute()
        self.ncpu = int(self.config.as_list("Process", "NumberCpu")[0])
        self.fix_l0_time_tag = False
        if (
            hasattr(self.l1b_geo_config, "fix_l0_time_tag")
            and self.l1b_geo_config.fix_l0_time_tag
        ):
            self.fix_l0_time_tag = True
        self.orb = create_orbit_raw(
            self.config,
            pos_off=self.l1b_geo_config.x_offset_iss,
            extrapolation_pad=self.l1b_geo_config.extrapolation_pad,
            large_gap=self.l1b_geo_config.large_gap,
            fix_l0_time_tag=self.fix_l0_time_tag,
        )
        self.dem = create_dem(self.config)
        self.lwm = create_lwm(self.config)
        self.ortho_base_dir: Path = ortho_base_directory(self.config)
        self.radlist = [
            Path(i).absolute() for i in self.config.as_list("InputFileGroup", "L1B_RAD")
        ]
        self.prod_dir = Path(
            self.config.as_list("ProductPathGroup", "ProductPath")[0]
        ).absolute()
        self.read_version()
        self.file_version = self.config.as_list("ProductPathGroup", "ProductCounter")[0]
        self.build_id = self.config.as_list("PrimaryExecutable", "BuildID")[0]
        self.collection_label = self.config.as_list(
            "ProductPathGroup", "CollectionLabel"
        )[0]
        self.orbfname = Path(
            self.config.as_list("TimeBasedFileGroup", "L1A_RAW_ATT")[0]
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
        self.prod_dir = prod_dir.absolute()
        self.ncpu = number_cpu
        self.file_version = "01"
        self.fix_l0_time_tag = False
        if (
            hasattr(self.l1b_geo_config, "fix_l0_time_tag")
            and self.l1b_geo_config.fix_l0_time_tag
        ):
            self.fix_l0_time_tag = True
        self.orbfname = l1a_raw_att.absolute()
        if self.fix_l0_time_tag:
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

    def line_order_reversed(self, radfname: Path) -> bool:
        """Determine if the line order is reversed in radfname. Also check that
        this matches any previous line_order_reversed setting."""
        line_order_reversed = False
        if (
            as_string(h5py.File(radfname, "r")["/L1B_RADMetadata/RadScanLineOrder"][()])
            == "Reverse line order"
        ):
            line_order_reversed = True
        if (
            self._line_order_reversed is not None
            and self._line_order_reversed != line_order_reversed
        ):
            raise RuntimeError(
                "Currently require that all L1B_RAD given to l1b_geo_process have the same line ordering (/L1B_RADMetadata/RadScanLineOrder)"
            )
        self._line_order_reversed = line_order_reversed
        return self._line_order_reversed

    def igc(
        self, radfname: Path, include_image: bool, eband: int
    ) -> EcostressImageGroundConnection:
        orbit, scene, acquisition_time = orbit_from_metadata(radfname)
        tt = create_time_table(
            radfname, self.l1b_geo_config.mirror_rpm, self.l1b_geo_config.frame_time
        )
        sm = create_scan_mirror(
            radfname,
            self.l1b_geo_config.max_encoder_value,
            self.l1b_geo_config.first_encoder_value_0,
            self.l1b_geo_config.second_encoder_value_0,
            self.l1b_geo_config.instrument_to_sc_euler,
            self.l1b_geo_config.first_angle_per_encoder_value,
            self.l1b_geo_config.second_angle_per_encoder_value,
        )
        self.cam.line_order_reversed = self.line_order_reversed(radfname)
        img: None | geocal.RasterImage = None
        if include_image:
            if eband == 0:
                img = geocal.GdalRasterImage(f'HDF5:"{radfname}"://SWIR/swir_dn')
            else:
                img = geocal.GdalRasterImage(
                    f'HDF5:"{radfname}"://Radiance/radiance_{eband}'
                )
                img = geocal.ScaleImage(img, 100.0)
        igc = EcostressImageGroundConnection(
            self.orb, tt, self.cam, sm, self.dem, img, f"Scene {scene}"
        )
        return igc

    def filter_scene_failure(self, radlist: list[Path]) -> list[Path]:
        """We have a set of set of scene failures that we want to handle by
        just skipping the scenes. Go through and remove these scenes before
        we do anything else."""
        radfname_ok: list[Path] = []
        for radfname in radlist:
            orbit, scene, acquisition_time = orbit_from_metadata(radfname)
            igc = self.igc(radfname, include_image=False, eband=-1)
            # Check that we have no large gaps in the time
            nspace = int(
                math.ceil(
                    (igc.time_table.max_time - igc.time_table.min_time)
                    / (self.l1b_geo_config.large_gap - 1.0)
                )
            )
            try:
                for tm in np.linspace(
                    igc.time_table.min_time.j2000, igc.time_table.max_time.j2000, nspace
                ):
                    t = geocal.Time.time_j2000(tm)
                    if t >= igc.orbit.min_time and t <= igc.orbit.max_time:
                        _ = igc.orbit.orbit_data(t)
            except RuntimeError as e:
                if "Request time is in the middle of a large gap" in str(e):
                    logger.warning(
                        f"Large gap found in {igc.title}. Skipping this scene"
                    )
                    continue
                else:
                    raise
            # Check if we cross the dateline. We don't currently handle this.
            # We could possibly add support, but geotiff doesn't work across
            # the dateline either so we would need to think carefully how to
            # do this. For now just skip these scenes.
            try:
                if igc.crosses_dateline:
                    logger.warning(f"Crossing dateline in {scene}. Skipping this scene")
                    continue
            except RuntimeError as e:
                if "Out of range error" in str(e):
                    logger.warning(f"Crossing dateline in {scene}. Skipping this scene")
                    continue
                else:
                    raise

            # Passed all the tests, to add to list of what we process
            radfname_ok.append(radfname)

        return radfname_ok

    def determine_output_file_name(self) -> None:
        """Create the list of output files. Also set up the qa_file"""
        self.inlist = [
            str(self.orbfname),
        ]
        self.inlist.extend([str(i) for i in self.radlist])
        self.inlist.append(str(self.l1_osp_dir / "l1b_geo_config.py"))
        self.ofile: list[Path] = []
        self.ofile_map: list[Path] = []
        self.ofile_kmz: list[Path] = []
        self.is_day: list[bool] = []
        self.ortho_base: list[geocal.CartLabMultifile] = []
        self.scene_list: list[int] = []
        first_file = True
        for radfname in self.radlist:
            orbit, scene, acquisition_time = orbit_from_metadata(radfname)
            self.ofile.append(
                Path(
                    ecostress_file_name(
                        "L1B_GEO",
                        orbit,
                        scene,
                        acquisition_time,
                        build=self.build_id,
                        collection_label=self.collection_label,
                        version=self.file_version,
                    )
                )
            )
            self.ofile_map.append(
                Path(
                    ecostress_file_name(
                        "L1B_MAP_RAD",
                        orbit,
                        scene,
                        acquisition_time,
                        build=self.build_id,
                        collection_label=self.collection_label,
                        version=self.file_version,
                    )
                )
            )
            self.ofile_kmz.append(
                Path(
                    ecostress_file_name(
                        "L1B_KMZ_MAP",
                        orbit,
                        scene,
                        acquisition_time,
                        build=self.build_id,
                        collection_label=self.collection_label,
                        extension=".kmz",
                        version=self.file_version,
                        intermediate=True,
                    )
                )
            )
            if (
                not self.force_night
                and as_string(
                    h5py.File(radfname, "r")["StandardMetadata/DayNightFlag"][()]
                )
                == "Day"
            ):
                self.is_day.append(True)
                eband = self.eband_day
                lband = self.lband_day
                self.ortho_base.append(self.ortho_base_day)
            else:
                self.is_day.append(False)
                eband = self.eband_night
                lband = self.lband_night
                self.ortho_base.append(self.ortho_base_night)
            logger.info(
                "Scene %d is %s, matching ecostress band %d to Landsat band %d"
                % (scene, "Day" if self.is_day[-1] else "Night", eband, lband)
            )
            self.scene_list.append(scene)
            if first_file:
                first_file = False
                self.l1b_att_fname = Path(
                    ecostress_file_name(
                        "L1B_ATT",
                        orbit,
                        None,
                        acquisition_time,
                        collection_label=self.collection_label,
                        build=self.build_id,
                        version=self.file_version,
                    )
                )
                self.qa_fname = Path(
                    ecostress_file_name(
                        "L1B_GEO_QA",
                        orbit,
                        None,
                        acquisition_time,
                        collection_label=self.collection_label,
                        build=self.build_id,
                        version=self.file_version,
                        intermediate=True,
                    )
                )
        self.qa_file = L1bGeoQaFile(self.qa_fname.absolute(), self.log_string_handle)
        self.qa_file.input_list(
            str(self.l1_osp_dir / "l1b_geo_config.py"),
            str(self.orbfname),
            [str(i) for i in self.radlist],
        )

    def create_igccol_initial(self) -> EcostressIgcCollection:
        igccol = EcostressIgcCollection()
        for i, radfname in enumerate(self.radlist):
            igc = self.igc(
                radfname,
                include_image=True,
                eband=(self.eband_day if self.is_day[i] else self.eband_night),
            )
            # Kludge to run with subsetted data. We only want to do this for the Landsat
            # fill in white paper (at least for now), so not worth proving an actual interface
            # here. We just hard code using subsetted data when we want that for testing.
            if True:
                igccol.add_igc(igc)
            else:
                igccol.add_igc(EcostressImageGroundConnectionSubset(igc, 1400, 2600))
        return igccol

    def collect_qa(
        self,
        igccol: EcostressImageGroundConnection,
        tpcol: geocal.TiePointCollection | None,
        pass_number: int,
    ) -> None:
        """Collect information on the time of correction before and after scene,
        and populate QA file with this."""
        if self.qa_file is None:
            return
        if pass_number == 1:
            for i in range(igccol.number_image):
                assert self._line_order_reversed is not None
                igc = igccol.image_ground_connection(i)
                self.qa_file.write_igc_xml(
                    f"Scene {self.scene_list[i]}",
                    igc.scan_mirror,
                    igc.time_table,
                    self._line_order_reversed,
                )
        self.tcorr_before = []
        self.tcorr_after = []
        self.geo_qa = []
        for i in range(igccol.number_image):
            igc = igccol.image_ground_connection(i)
            if hasattr(igc, "time_table"):
                tt = igc.time_table
            else:
                tt = igc.sub_time_table
            t = tt.min_time + (tt.max_time - tt.min_time)
            t1 = -9999.0
            t2 = -9999.0
            # Get points, but only if we actually have at
            # least on correction point
            if len(igc.orbit.parameter) > 0:
                tb, ta = igccol.nearest_attitude_time_point(t)
                if tb < geocal.Time.max_valid_time - 1:
                    t1 = t - tb
                if ta < geocal.Time.max_valid_time - 1:
                    t2 = ta - t
            self.tcorr_before.append(t1)
            self.tcorr_after.append(t2)
            self.geo_qa.append(self.l1b_geo_config.geocal_accuracy_qa(t1, t2))
            logger.info(
                f"Scene {self.scene_list[i]} geolocation accuracy QA: {self.geo_qa[-1]}"
            )

        # Write out QA data
        if tpcol:
            self.qa_file.add_final_accuracy(
                pass_number,
                igccol,
                tpcol,
                self.tcorr_before,
                self.tcorr_after,
                self.geo_qa,
            )
        self.qa_file.add_orbit(pass_number, igccol.image_ground_connection(0).orbit)
        # TODO Add support for multiple passes. Although maybe it doesn't matter,
        # we don't ever do anything with this. Maybe just the original igccol_initial
        # and final tpcol, igcol_sba, tpcol_sba. Think about this
        self.qa_file.write_xml(
            pass_number,
            f"igccol_initial_pass_{pass_number}.xml",
            f"tpcol_pass_{pass_number}.xml",
            f"igccol_sba_pass_{pass_number}.xml",
            f"tpcol_sba_pass_{pass_number}.xml",
        )

    def generate_output(
        self,
        igccol: EcostressImageGroundConnection,
        tpcol: geocal.TiePointCollection | None,
        pool: Pool | None,
    ) -> None:
        """Once we have the final corrected igccol, generate all the output"""
        avg_md = np.full((len(self.radlist), 3), -9999.0)
        for i, radfname in enumerate(self.radlist):
            logger.info(f"Doing scene number {self.scene_list[i]}")
            fin = h5py.File(radfname, "r")
            if "BandSpecification" in fin["L1B_RADMetadata"]:
                nband = np.count_nonzero(
                    fin["L1B_RADMetadata/BandSpecification"][:] > 0
                )
            else:
                nband = 6
            if (
                igccol.image_ground_connection(i).number_good_scan
                < self.l1b_geo_config.min_number_good_scan
            ):
                logger.info(
                    f"Scene number {self.scene_list[i]} has only {igccol.image_ground_connection(i).number_good_scan} good scans. We require a minimum of {self.l1b_geo_config.min_number_good_scan}. Skipping output for this scene"
                )
            elif igccol.image_ground_connection(i).crosses_dateline:
                logger.info(
                    f"Scene number {self.scene_list[i]} crosses date line. We don't handle this. Skipping output for this scene"
                )
            else:
                # Short term allow this to fail, just so we can process old data
                # which didn't have FieldOfViewObstruction (added in B7)
                try:
                    field_of_view_obscured = h5py.File(radfname, "r")[
                        "/StandardMetadata/FieldOfViewObstruction"
                    ][()]
                except KeyError:
                    field_of_view_obscured = "NO"
                # We actually want to generate the cloud mask upstream of this,
                # when we are doing the original tiepoint collection. But for
                # now tuck this in here, so we can get the basics of this running
                # and make this part of our processing chain.
                cprocess = CloudProcessing(
                    self.l1_osp_dir / self.l1b_geo_config.rad_lut_fname,
                    self.l1_osp_dir / self.l1b_geo_config.b11_lut_file_pattern,
                )
                l1bgeo = L1bGeoGenerate(
                    igccol.image_ground_connection(i),
                    cprocess,
                    radfname,
                    self.lwm,
                    self.ofile[i],
                    self.inlist,
                    self.is_day[i],
                    field_of_view_obscured=field_of_view_obscured,
                    number_line=self.number_line,
                    run_config=self.config,
                    collection_label=self.collection_label,
                    build_id=self.build_id,
                    pge_version=self.pge_version["l1b_geo"],
                    correction_done=self.correction_done,
                    tcorr_before=self.tcorr_before[i],
                    tcorr_after=self.tcorr_after[i],
                    geolocation_accuracy_qa=self.geo_qa[i],
                )
                l1bgeo.run(pool)
                avg_md[i, 0] = l1bgeo.avg_sz
                avg_md[i, 1] = l1bgeo.oa_lf
                avg_md[i, 2] = l1bgeo.cloud_cover
                if self.l1b_geo_config.generate_map_product:
                    logger.info(
                        f"Generating Map Product scene number {self.scene_list[i]}"
                    )
                    l1bgeo_map = L1bGeoGenerateMap(
                        l1bgeo,
                        str(radfname),
                        str(self.ofile_map[i]),
                        north_up=self.l1b_geo_config.north_up,
                        resolution=self.l1b_geo_config.map_resolution,
                        number_subpixel=self.l1b_geo_config.map_number_subpixel,
                    )
                    l1bgeo_map.run()
                if self.l1b_geo_config.generate_kmz_file:
                    logger.info(
                        f"Generating KMZ file scene number {self.scene_list[i]}"
                    )
                    band_list = (
                        self.l1b_geo_config.kmz_band_list_5band
                        if (nband == 6)
                        else self.l1b_geo_config.kmz_band_list_3band
                    )
                    l1bgeo_kmz = L1bGeoGenerateKmz(
                        l1bgeo,
                        str(radfname),
                        str(self.ofile_kmz[i]),
                        band_list=band_list,
                        use_jpeg=self.l1b_geo_config.kmz_use_jpeg,
                        resolution=self.l1b_geo_config.kmz_resolution,
                        thumbnail_size=self.l1b_geo_config.kmz_thumbnail_size,
                        number_subpixel=self.l1b_geo_config.kmz_number_subpixel,
                    )
                    l1bgeo_kmz.run()

        if self.qa_file is not None:
            self.qa_file.add_average_metadata(avg_md)

        # Write out updated orbit data
        fin = h5py.File(self.orbfname, "r")
        tatt = [geocal.Time.time_j2000(t) for t in fin["Attitude/time_j2000"][:]]
        teph = [geocal.Time.time_j2000(t) for t in fin["Ephemeris/time_j2000"][:]]
        l1batt = L1bAttGenerate(
            self.orbfname,
            igccol.image_ground_connection(0).orbit,
            str(self.l1b_att_fname),
            tatt,
            teph,
            self.inlist,
            self.qa_file,
            run_config=self.config,
            collection_label=self.collection_label,
            build_id=self.build_id,
            pge_version=self.pge_version["l1b_geo"],
            correction_done=self.correction_done,
        )
        l1batt.run()

    def collect_tp(
        self, igccol: EcostressIgcCollection, pool: Pool | None, pass_number: int
    ) -> tuple[geocal.TiePointCollection, list[tuple[int, geocal.Time, geocal.Time]]]:
        t = L1bTpCollect(
            igccol,
            self.ortho_base,
            self.lwm,
            self.qa_file,
            fftsize=self.l1b_geo_config.fftsize,
            magnify=self.l1b_geo_config.magnify,
            magmin=self.l1b_geo_config.magmin,
            toler=self.l1b_geo_config.toler,
            redo=self.l1b_geo_config.redo,
            ffthalf=self.l1b_geo_config.ffthalf,
            seed=self.l1b_geo_config.seed,
            num_x=self.l1b_geo_config.num_x,
            num_y=self.l1b_geo_config.num_y,
            proj_number_subpixel=self.l1b_geo_config.proj_number_subpixel,
            # min_tp_per_scene=self.l1b_geo_config.min_tp_per_scene,
            min_tp_per_scene=80
            if pass_number == 1
            else self.l1b_geo_config.min_tp_per_scene,
            min_number_good_scan=self.l1b_geo_config.min_number_good_scan,
            pass_number=pass_number,
        )
        tpcol, time_range_tp = t.tpcol(pool=pool)
        return tpcol, time_range_tp

    def add_breakpoint(
        self,
        orb: geocal.OrbitOffsetCorrection,
        time_range_tp: list[tuple[int, geocal.Time, geocal.Time]],
        pass_number: int,
    ) -> None:
        """Add breakpoints for the scenes that we got good tiepoints from.
        We may well tweak this, but right now we set breakpoints at the
        beginning, middle and end of the scene, unless the beginning
        is within one scene of another breakpoint."""
        if pass_number == 1:
            for i, tmin, tmax in time_range_tp:
                orb.add_scene(self.scene_list[i], tmin, tmax)
        else:
            # For further passes, add any new scenes we have tiepoints for,
            # but start with the value we current have at those time points
            for i, tmin, tmax in time_range_tp:
                if self.scene_list[i] not in orb.scene_list:
                    orb.add_scene(self.scene_list[i], tmin, tmax, True)

    def run_sba(
        self,
        igccol: EcostressIgcCollection,
        tpcol: geocal.TiePointCollection,
        pass_number: int,
    ) -> EcostressIgcCollection:
        """Run the SBA to improve the orbit"""
        try:
            geocal.write_shelve(f"tpcol_pass_{pass_number}.xml", tpcol)
            geocal.write_shelve(f"igccol_initial_pass_{pass_number}.xml", igccol)
            with logger.catch(reraise=True):
                process_run(
                    [
                        "sba",
                        "--verbose",
                        "--hold-gcp-fixed",
                        "--gcp-sigma=50",
                        f"igccol_initial_pass_{pass_number}.xml",
                        f"tpcol_pass_{pass_number}.xml",
                        f"igccol_sba_pass_{pass_number}.xml",
                        f"tpcol_sba_pass_{pass_number}.xml",
                    ],
                )
                self.correction_done = True
                return geocal.read_shelve(f"igccol_sba_pass_{pass_number}.xml")
        except Exception:
            if not self.l1b_geo_config.continue_on_sba_fail:
                raise
            logger.warning(
                "SBA/Tiepoint failed to correct orbit data. Continue processing without correction."
            )
            return igccol

    def correct_igc(
        self, igccol: EcostressIgcCollection, pool: Pool | None, pass_number: int
    ) -> tuple[EcostressIgcCollection, geocal.TiePointCollection | None]:
        """Collect tie points, and used to correct the igccol"""
        logger.info(f"Starting pass {pass_number}")
        tpcol, time_range_tp = self.collect_tp(igccol, pool, pass_number)
        if len(tpcol) == 0:
            logger.info("No tie-points, so skipping SBA correction")
            tpcol = None
            return igccol, None
        self.add_breakpoint(self.orb, time_range_tp, pass_number)
        igccol_corrected = self.run_sba(igccol, tpcol, pass_number)
        # Update orbit and camera, if we updated the igccol
        self.orb = igccol_corrected.image_ground_connection(0).orbit
        self.cam = igccol_corrected.image_ground_connection(0).camera
        logger.info(f"Done with pass {pass_number}")
        return igccol_corrected, tpcol

    def run(self) -> None:
        """Run the L1bGeoProcess"""
        geocal.makedirs_p(str(self.prod_dir))
        curdir = os.getcwd()
        pool = None
        try:
            os.chdir(self.prod_dir)
            # Set up logger
            logger.add(self.log_file, level="DEBUG")
            # Capture log messages, we store this in the qa file
            self.log_string_handle = io.StringIO()
            logger.add(self.log_string_handle, level="DEBUG")
            if self.ncpu > 1:
                pool = Pool(self.ncpu)
            # Create python needed so geocal can load ecostress objects
            with open("extra_python_init.py", "w") as fh:
                print("from ecostress import *\n", file=fh)

            if self.fix_l0_time_tag:
                logger.info("Applying Fix to incorrect L0 time tags")
            self.radlist = self.filter_scene_failure(self.radlist)
            self.determine_output_file_name()
            tpcol: geocal.TiePointCollection | None = None

            igccol_initial = self.create_igccol_initial()

            if self.igccol_use is not None:
                # For testing, skip actually doing image matching and
                # use existing results
                igccol_corrected = geocal.read_shelve(str(self.igccol_use))
                if self.tpcol_use is not None:
                    tpcol = geocal.read_shelve(str(self.tpcol_use))
                self.collect_qa(igccol_corrected, tpcol, pass_number=1)
            elif not (self.skip_sba or self.l1b_geo_config.skip_sba):
                igccol_corrected_pass1, tpcol_pass1 = self.correct_igc(
                    igccol_initial, pool, pass_number=1
                )
                self.collect_qa(igccol_corrected_pass1, tpcol_pass1, pass_number=1)
                igccol_corrected, tpcol = self.correct_igc(
                    igccol_corrected_pass1, pool, pass_number=2
                )
                self.collect_qa(igccol_corrected, tpcol, pass_number=2)
            else:
                igccol_corrected = igccol_initial
                self.collect_qa(igccol_corrected, tpcol, pass_number=1)

            # Generate output once we have the final igccol
            self.generate_output(igccol_corrected, tpcol, pool)
        finally:
            if pool is not None:
                pool.close()
            if self.qa_file is not None:
                self.qa_file.close()
            os.chdir(curdir)


__all__ = [
    "L1bGeoProcess",
]
