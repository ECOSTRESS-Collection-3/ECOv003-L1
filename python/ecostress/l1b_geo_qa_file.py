from __future__ import annotations
import h5py  # type: ignore
import os
from pathlib import Path
import gzip
import re
import numpy as np
import subprocess
import geocal  # type: ignore
from ecostress_swig import (  # type: ignore
    EcostressScanMirror,
    EcostressOrbit,
    EcostressImageGroundConnection,
    EcostressIgcCollection,
)
import pandas as pd
import types
import sys
import typing
from typing import Any

if typing.TYPE_CHECKING:
    import io
    from .geo_write_standard_metadata import GeoWriteStandardMetadata


class L1bGeoQaFile(object):
    """This is the L1bGeoQaFile. We have a separate class just to make it
    easier to interface with."""

    def __init__(
        self,
        fname: str | os.PathLike[str],
        log_string_handle: io.StringIO,
        local_granule_id: str | None = None,
    ) -> None:
        self.fname = Path(fname)
        self.log_string_handle = log_string_handle
        self.scene_name: list[str] | None = None
        self.tp_stat: dict[int, np.ndarray] = {}
        self.encountered_exception = False
        if local_granule_id:
            self.local_granule_id = local_granule_id
        else:
            self.local_granule_id = os.path.basename(fname)
        # This ends up getting pickled, and h5py doesn't pickle well. So
        # instead of keeping the file open, we reopen and update as needed.

        fout = h5py.File(fname, "w")
        fout.create_group("Logs")
        fout.create_group("Orbit")
        fout.create_group("PythonObject")
        fout.create_group("Tiepoint")
        fout.create_group("Accuracy Estimate")
        fout.close()

    def write_igc_xml(
        self,
        scene_name: str,
        sm: EcostressScanMirror,
        tt: geocal.TimeTable,
        line_order_reversed: bool,
    ) -> None:
        """Store the scan mirror and time table as XML that we can reload.
        This is nice so we can create a Igc without the Raster Image without needing
        to open the relatively large L1B Radiance file. If you need the actual
        image data, you should just directly use the L1B Radiance file rather
        than these objects"""
        with h5py.File(self.fname, "a") as f:
            g = f["PythonObject"].create_group(scene_name)
            geocal.serialize_write_string(sm)
            g.create_dataset(
                "scan_mirror",
                data=np.void(
                    gzip.compress(geocal.serialize_write_string(sm).encode("utf8"))
                ),
            )
            g.create_dataset(
                "time_table",
                data=np.void(
                    gzip.compress(geocal.serialize_write_string(tt).encode("utf8"))
                ),
            )
            g["Line Order Reversed"] = str(line_order_reversed)

    def write_xml(
        self,
        pass_number: int,
        igc_initial: str,
        tpcol: str,
        igc_sba: str,
        tpcol_sba: str,
    ) -> None:
        """Write the xml serialization files. Note because these are large
        we compress them. HDF5 does compression, but not apparently on
        strings. You can access them, but need to manually decompress.
        Note also the serialization has hardcoded paths in them, so often
        you can't use this directly. But writing out as a file to examine
        can be useful.

        Also, we could just directly use the binary serialization. But I'm
        guessing that the xml is more portable. In any case, the compressed
        xml is about the same size as the binary serialization.

        To directly create the serialized objects, do something like:

        import ecostress
        import geocal
        import h5py
        import gzip
        t = h5py.File("test_qa.h5", "r")["PythonObject/igccol_initial"][()]
        igccol_initial = geocal.serialize_read_generic_string(gzip.decompress(t).decode('utf8'))
        """
        with h5py.File(self.fname, "a") as f:
            data = []
            desc = []
            for inf in (igc_initial, tpcol, igc_sba, tpcol_sba):
                try:
                    data.append(open(inf, "r").read().encode("utf8"))
                except FileNotFoundError:
                    data.append(b"")
                try:
                    desc.append(
                        subprocess.run(
                            ["shelve_show", inf],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                        ).stdout
                    )
                except FileNotFoundError:
                    desc.append(b"")
            g = f["PythonObject"].create_group(f"Pass {pass_number}")
            # Note, we compress the data ourselves. While HDF5 supports
            # compression, it doesn't seem to do this with strings.
            for i, fout in enumerate(
                ["igccol_initial", "tpcol", "igccol_sba", "tpcol_sba"]
            ):
                g.create_dataset(fout, data=np.void(gzip.compress(data[i])))
                g.create_dataset(
                    fout + "_desc", data=desc[i], dtype=h5py.special_dtype(vlen=bytes)
                )

    def input_list(self, config_fname: str, orbfname: str, radlist: list[str]) -> None:
        with h5py.File(self.fname, "a") as f:
            g = f.create_group("Input File")
            g.create_dataset(
                "Config Filename",
                data=[
                    config_fname.encode("utf8"),
                ],
                dtype=h5py.special_dtype(vlen=bytes),
            )
            g.create_dataset(
                "Orbit Filename",
                data=[
                    orbfname.encode("utf8"),
                ],
                dtype=h5py.special_dtype(vlen=bytes),
            )
            g.create_dataset(
                "L1B Radiance Filename",
                data=[i.encode("utf8") for i in radlist],
                dtype=h5py.special_dtype(vlen=bytes),
            )

    def add_average_metadata(self, avg_md: np.ndarray) -> None:
        """Add average metadata. First column is average solar zenith angle,
        second is overall land fraction, third is cloud coverage. We have one row per scene"""
        with h5py.File(self.fname, "a") as f:
            d = f.create_dataset("Average Metadata", data=avg_md)
            d.attrs[
                "Description"
            ] = """This is the average metadata. We have one row for each scene. 

The first column is the average solar zenith angle, in degrees. The
second column is the overall land fraction for the scene, as a percentage.
The third column is the cloud cover, as a percentage."""

    def add_orbit(self, pass_number: int, orb: geocal.Orbit) -> None:
        """Add data about orbit. Note that this requires we use
        OrbitOffsetCorrection, it doesn't work otherwise."""
        if hasattr(orb, "orbit_offset_correction"):
            atime, acorr, ptime, pcorr = (
                orb.orbit_offset_correction.orbit_correction_parameter()
            )
        else:
            atime, acorr, ptime, pcorr = orb.orbit_correction_parameter()
        with h5py.File(self.fname, "a") as f:
            orb_group = f["Orbit"].create_group(f"Pass {pass_number}")
            d = orb_group.create_dataset(
                "Attitude Time Point", data=np.array([t.j2000 for t in atime])
            )
            d.attrs["Units"] = "s"
            d = orb_group.create_dataset(
                "Position Time Point", data=np.array([t.j2000 for t in ptime])
            )
            d.attrs["Units"] = "s"
            d = orb_group.create_dataset("Attitude Correction", data=acorr)
            d.attrs["Units"] = "arcseconds"
            d.attrs[
                "Description"
            ] = """This is the attitude correction, one row per time point. 
The columns are yaw, pitch, and roll in arceconds."""
            d = orb_group.create_dataset("Position Correction", data=pcorr)
            d.attrs["Units"] = "m"
            d.attrs[
                "Description"
            ] = """This is the position correction, one row per time point.
Position is in ECR, in meters. The columns are X, Y, and Z 
offset."""

    def add_tp_log(self, pass_number: int, scene_name: str, tplogfname: str) -> None:
        """Add a TP log file"""
        try:
            log = open(tplogfname, "r").read()
        except FileNotFoundError:
            # Ok if log file isn't found, just given an message
            log = "log file missing"
        with h5py.File(self.fname, "a") as f:
            gname = f"Tiepoint Logs Pass {pass_number}"
            if gname not in f["Logs"]:
                tplog_group = f["Logs"].create_group(gname)
            else:
                tplog_group = f[f"Logs/{gname}"]
            tplog_group.create_dataset(
                scene_name, data=log, dtype=h5py.special_dtype(vlen=bytes)
            )

    def add_tp_single_scene(
        self,
        pass_number: int,
        image_index: int,
        igccol: geocal.IgcCollection,
        tpcol: geocal.TiePointCollection,
        ntpoint_initial: int,
        ntpoint_removed: int,
        ntpoint_final: int,
        number_match_try: int,
    ) -> None:
        """Write out information about the tiepoints we collect for scene."""
        if self.scene_name is None:
            self.scene_name = [
                igccol.title(i).encode("utf8") for i in range(igccol.number_image)
            ]
        if pass_number not in self.tp_stat:
            self.tp_stat[pass_number] = np.full((igccol.number_image, 9), -9999.0)
        self.tp_stat[pass_number][image_index, 0] = ntpoint_initial
        self.tp_stat[pass_number][image_index, 1] = ntpoint_removed
        self.tp_stat[pass_number][image_index, 2] = ntpoint_final
        self.tp_stat[pass_number][image_index, 3] = number_match_try
        if len(tpcol) > 0:
            df = tpcol.data_frame(igccol, image_index)
            self.tp_stat[pass_number][image_index, 4] = df.ground_2d_distance.quantile(
                0.68
            )
        tpdata = None
        if len(tpcol) > 0:
            tpdata = np.empty((len(tpcol), 5))
        for i, tp in enumerate(tpcol):
            ic = tp.image_coordinate(image_index)
            assert tpdata is not None
            tpdata[i, 0:2] = ic.line, ic.sample
            tpdata[i, 2:6] = geocal.Ecr(tp.ground_location).position
        with h5py.File(self.fname, "a") as f:
            tpgname = f"Pass {pass_number}"
            if tpgname not in f["Tiepoint"]:
                tp_group = f["Tiepoint"].create_group(tpgname)
                tp_group.create_dataset(
                    "Scenes", data=self.scene_name, dtype=h5py.special_dtype(vlen=bytes)
                )
            else:
                tp_group = f["Tiepoint"][tpgname]
            s_group = tp_group.create_group(igccol.title(image_index))
            if tpdata is not None:
                d = s_group.create_dataset("Tiepoints", data=tpdata)
                d.attrs[
                    "Description"
                ] = """This is the list of tiepoints for a scene, after removing blunders.

The first column in image coordinate line, the second column is image
coordinate sample.

The remaining three columns are the location of the ground coordinate in
the reference image, in Ecr coordinates (in meters).
"""

    def add_final_accuracy(
        self,
        pass_number: int,
        igccol_corrected: geocal.IgcCollection,
        tpcol: geocal.TiePointCollection,
        tcor_before: list[float],
        tcor_after: list[float],
        geo_qa: list[str],
    ) -> None:
        # Ok if no tiepoints for scene i, this just return nan
        t = np.array(
            [
                tpcol.data_frame(igccol_corrected, i).ground_2d_distance.quantile(0.68)
                for i in range(igccol_corrected.number_image)
            ]
        )
        t[np.isnan(t)] = -9999
        # Normally already filled in, but in testing we might call add_final_accuracy
        # without any of the add_tp_single_scene (e.g., we are skipping doing the
        # image matching for a test
        if pass_number not in self.tp_stat:
            self.tp_stat[pass_number] = np.full(
                (igccol_corrected.number_image, 9), -9999.0
            )
        self.tp_stat[pass_number][:, 5] = t
        self.tp_stat[pass_number][:, 6] = tcor_before
        self.tp_stat[pass_number][:, 7] = tcor_after
        for i in range(self.tp_stat[pass_number].shape[0]):
            if geo_qa[i] == "Best":
                self.tp_stat[pass_number][i, 8] = 0
            elif geo_qa[i] == "Good":
                self.tp_stat[pass_number][i, 8] = 1
            elif geo_qa[i] == "Suspect":
                self.tp_stat[pass_number][i, 8] = 2
            elif geo_qa[i] == "Poor":
                self.tp_stat[pass_number][i, 8] = 3
            else:
                self.tp_stat[pass_number][i, 8] = -9999

    def write_standard_metadata(self, m: GeoWriteStandardMetadata) -> None:
        """Write out standard metadata for QA file. Since this is almost
        identical to the metadata we have for the l1b_att file, we pass in
        the metadata for that file and just change a few things before
        writing it out."""
        # We copy the metadata, just changing the file we attach this to
        # and the local granule id
        with h5py.File(self.fname, "a") as f:
            mcopy = m.copy_new_file(f, self.local_granule_id, "L1B_GEO_QA")
            mcopy.write()

    def close(self) -> None:
        """Finishing writing up data, and close file"""
        if self.log_string_handle is not None:
            log = self.log_string_handle.getvalue()
        else:
            log = "log file missing"
        with h5py.File(self.fname, "a") as f:
            log_group = f["Logs"]
            dset = log_group.create_dataset(
                "Overall Log", data=log, dtype=h5py.special_dtype(vlen=bytes)
            )
            if self.encountered_exception:
                dset = log_group.create_dataset(
                    "Encountered Exception",
                    data="True",
                    dtype=h5py.special_dtype(vlen=bytes),
                )
            else:
                dset = log_group.create_dataset(
                    "Encountered Exception",
                    data="False",
                    dtype=h5py.special_dtype(vlen=bytes),
                )
            if self.tp_stat is not None:
                for pass_number in sorted(self.tp_stat.keys()):
                    tpgname = f"Pass {pass_number}"
                    if tpgname not in f["Tiepoint"]:
                        tp_group = f["Tiepoint"].create_group(tpgname)
                    else:
                        tp_group = f["Tiepoint"][tpgname]
                    dset = tp_group.create_dataset(
                        "Tiepoint Count",
                        data=self.tp_stat[pass_number][:, 0:4].astype(np.int32),
                    )
                    dset.attrs[
                        "Description"
                    ] = """First column is the initial number of tie points

Second column is the number of blunders removed

Third column is the number after removing blunders and applying minimum
number of tiepoints (so if < threshold we set this to 0).

Fourth column is the number to image matching tries we did."""
            ac_group = f["Accuracy Estimate"]
            ac_group.create_dataset(
                "Scenes", data=self.scene_name, dtype=h5py.special_dtype(vlen=bytes)
            )
            if self.tp_stat is not None:
                for pass_number in sorted(self.tp_stat.keys()):
                    ac_pass_group = ac_group.create_group(f"Pass {pass_number}")
                    dset = ac_pass_group.create_dataset(
                        "Accuracy Before Correction",
                        data=self.tp_stat[pass_number][:, 4],
                    )
                    dset.attrs["Units"] = "m"
                    dset = ac_pass_group.create_dataset(
                        "Final Accuracy", data=self.tp_stat[pass_number][:, 5]
                    )
                    dset.attrs["Units"] = "m"
                    dset = ac_pass_group.create_dataset(
                        "Delta time correction before scene",
                        data=self.tp_stat[pass_number][:, 6],
                    )
                    dset.attrs["Units"] = "s"
                    dset = ac_pass_group.create_dataset(
                        "Delta time correction after scene",
                        data=self.tp_stat[pass_number][:, 7],
                    )
                    dset.attrs["Units"] = "s"
                    dset = ac_pass_group.create_dataset(
                        "Geolocation accuracy QA flag",
                        data=self.tp_stat[pass_number][:, 8],
                    )
                    dset.attrs[
                        "Description"
                    ] = """0: Best - Image matching was performed for this scene, expect 
       good geolocation accuracy.
1: Good - Image matching was performed on a nearby scene, and correction 
       has been interpolated/extrapolated. Expect good geolocation accuracy.
2: Suspect - Matched somewhere in the orbit. Expect better geolocation 
       than orbits w/o image matching, but may still have large errors.
3: Poor - No matches in the orbit. Expect largest geolocation errors.
9999: Unknown value"""

    @classmethod
    def _older_format(cls, fname: str | os.PathLike[str]) -> bool:
        f = h5py.File(fname, "r")
        return "Pass 1" not in f["PythonObject"]
        
    @classmethod
    def _read_obj(
        cls,
        fname: str | os.PathLike[str],
        name: str,
        scene_number: int | None = None,
        pass_number: int | None = None,
    ) -> Any:
        f = h5py.File(fname, "r")
        if cls._older_format(fname):
            t = f[f"PythonObject/{name}"][()]
        elif pass_number is None:
            t = f[f"PythonObject/Scene {scene_number}/{name}"][()]
        else:
            if f"Pass {pass_number}" not in f["PythonObject"]:
                raise RuntimeError(f"Pass {pass_number} not found in l1b_geo_qa file")
            t = f[f"PythonObject/Pass {pass_number}/{name}"][()]
        return geocal.serialize_read_generic_string(
            gzip.decompress(bytes(t)).decode("utf8")
        )

    @classmethod
    def scan_mirror(
        cls, fname: str | os.PathLike[str], scene_number: int
    ) -> EcostressScanMirror:
        if cls._older_format(fname):
            raise RuntimeError("scan_mirror is not available in collection 2 l1b_geo_qa")
        return cls._read_obj(fname, "scan_mirror", scene_number=scene_number)

    @classmethod
    def time_table(
        cls, fname: str | os.PathLike[str], scene_number: int
    ) -> geocal.TimeTable:
        if cls._older_format(fname):
            raise RuntimeError("time_table is not available in collection 2 l1b_geo_qa")
        return cls._read_obj(fname, "time_table", scene_number=scene_number)

    @classmethod
    def line_order_reversed(
        cls, fname: str | os.PathLike[str], scene_number: int
    ) -> bool:
        if cls._older_format(fname):
            raise RuntimeError("line_order_reversed is not available in collection 2 l1b_geo_qa")
        f = h5py.File(fname, "r")
        t = f[f"PythonObject/Scene {scene_number}/Line Order Reversed"][()].decode(
            "utf8"
        )
        return t == "True"

    @classmethod
    def tpcol(
        cls, fname: str | os.PathLike[str], pass_number: int = 2
    ) -> geocal.TimeTable:
        return cls._read_obj(fname, "tpcol", pass_number=pass_number)

    @classmethod
    def scene_list(cls, fname: str | os.PathLike[str]) -> list[int]:
        f = h5py.File(fname, "r")
        return [int(i[6:]) for i in f["/Accuracy Estimate/Scenes"][:]]

    @classmethod
    def config_filename(cls, fname: str | os.PathLike[str]) -> Path:
        f = h5py.File(fname, "r")
        return Path(f["/Input File/Config Filename"][()][0].decode("utf8"))

    @classmethod
    def orbit_filename(cls, fname: str | os.PathLike[str]) -> Path:
        f = h5py.File(fname, "r")
        if cls._older_format(fname):
            # Make use of specific order in input file list
            flist = f["/Input File List"]
            return Path(flist[0].decode("utf8"))
        return Path(f["/Input File/Orbit Filename"][()][0].decode("utf8"))

    @classmethod
    def l1b_rad_list(cls, fname: str | os.PathLike[str]) -> list[Path]:
        f = h5py.File(fname, "r")
        if cls._older_format(fname):
            # Make use of specific order in input file list
            flist = f["/Input File List"]
            return [Path(flist[i].decode("utf8")) for i in range(1,flist.shape[0]-1)]
        return [Path(i.decode("utf8")) for i in f["/Input File/Orbit Filename"][()]]

    @classmethod
    def l1b_geo_config(self, l1_osp_dir: str | os.PathLike[str]) -> types.ModuleType:
        try:
            sys.path.append(str(l1_osp_dir))
            import l1b_geo_config  # type: ignore

            return l1b_geo_config
        finally:
            sys.path.remove(str(l1_osp_dir))

    @classmethod
    def igccol(
        cls,
        fname: str | os.PathLike[str],
        l1_osp_dir: str | os.PathLike[str] | None = None,
        orbit_fname: str | os.PathLike[str] | None = None,
        l1b_rad_list: list[Path] | None = None,
        include_img: bool = False,
    ) -> EcostressIgcCollection:
        """This is the original igccol, without any breakpoints are updates.
        The l1b_geo_qa file has a list of the input files used when it was run, but
        often this is out of date. You can optionally supply a orbit_fname and/or l1b_rad_list.
        The l1b_rad_list is only needed if include_img if True."""
        # TODO Add support for including orbit corrections for each pass
        if cls._older_format(fname):
            raise RuntimeError("igccol is not available in collection 2 l1b_geo_qa")
        if l1_osp_dir is None:
            l1_osp_dir = cls.config_filename(fname).parent
        l1b_geo_config = cls.l1b_geo_config(l1_osp_dir)
        cam = geocal.read_shelve(str(Path(l1_osp_dir) / "camera.xml"))
        cam.mask_all_parameter()
        cam.focal_length = l1b_geo_config.camera_focal_length
        if orbit_fname is None:
            orbit_fname = cls.orbit_filename(fname)
        orb = EcostressOrbit(
            str(orbit_fname),
            l1b_geo_config.x_offset_iss,
            l1b_geo_config.extrapolation_pad,
            l1b_geo_config.large_gap,
        )
        dem = geocal.SrtmDem("", False)
        igccol = EcostressIgcCollection()
        for scn in cls.scene_list(fname):
            cam.line_order_reversed = cls.line_order_reversed(fname, scn)
            tt = cls.time_table(fname, scn)
            sm = cls.scan_mirror(fname, scn)
            img = None
            igc = EcostressImageGroundConnection(
                orb, tt, cam, sm, dem, img, f"Scene {scn}"
            )
            igccol.add_igc(igc)
        return igccol

    @classmethod
    def pass_list(cls, fname: str | os.PathLike[str]):
        if cls._older_format(fname):
            return ["Pass 1",]
        fh = h5py.File(fname, "r")
        return [i for i in list(fh["Accuracy Estimate"].keys()) if re.match(r"Pass", i)]

    @classmethod
    def data_frame(cls, fname: str | os.PathLike[str]) -> pd.DataFrame:
        """Return a pandas DataFrame with the contents of the QA file"""
        is_older = cls._older_format(fname)
        tlist = []
        t = pd.DataFrame(
            cls.scene_list(fname),
            columns=[
                "Scene",
            ],
        )
        tlist.append(t)
        fh = h5py.File(fname, "r")
        qa_val = {0: "Best", 1: "Good", 2: "Suspect", 3: "Poor", -9999: "Unknown"}
        plist = cls.pass_list(fname)
        for ps in plist:
            if is_older:
                d = fh["Tiepoint/Tiepoint Count"][:]
            else:
                d = fh[f"Tiepoint/{ps}/Tiepoint Count"][:]
            t2 = pd.DataFrame(
                d,
                columns=[
                    f"Initial Tiepoint {ps}",
                    f"Blunders {ps}",
                    f"Number Tiepoint {ps}",
                    f"Number Image Match Tries {ps}",
                ],
            )
            tlist.append(t2)
        for ps in plist:
            if is_older:
                d = fh["Accuracy Estimate/Accuracy Before Correction"][:]
            else:
                d = fh[f"Accuracy Estimate/{ps}/Accuracy Before Correction"][:]
            d[d < -9990] = np.NaN
            t3 = pd.DataFrame(
                d,
                columns=[
                    f"Initial Accuracy {ps}",
                ],
            )
            tlist.append(t3)
            if is_older:
                d = fh["Accuracy Estimate/Final Accuracy"][:]
            else:
                d = fh[f"Accuracy Estimate/{ps}/Final Accuracy"][:]
            d[d < -9990] = np.NaN
            t4 = pd.DataFrame(
                d,
                columns=[
                    f"Accuracy {ps}",
                ],
            )
            tlist.append(t4)
            if is_older:
                d = fh["Accuracy Estimate/Delta time correction before scene"][:]
            else:
                d = fh[f"Accuracy Estimate/{ps}/Delta time correction before scene"][:]
            t5 = pd.DataFrame(
                d,
                columns=[
                    f"Delta t before scene {ps}",
                ],
            )
            tlist.append(t5)
            if is_older:
                d = fh["Accuracy Estimate/Delta time correction after scene"][:]
            else:
                d = fh[f"Accuracy Estimate/{ps}/Delta time correction after scene"][:]
            t6 = pd.DataFrame(
                d,
                columns=[
                    f"Delta t after scene {ps}",
                ],
            )
            tlist.append(t6)
            if is_older:
                dv = fh["Accuracy Estimate/Geolocation accuracy QA flag"][:]
            else:
                dv = fh[f"Accuracy Estimate/{ps}/Geolocation accuracy QA flag"][:]
            t7 = pd.DataFrame(
                [
                    qa_val[v]
                    for v in dv
                ],
                columns=[
                    f"QA Flag {ps}",
                ],
            )
            tlist.append(t7)

        d = fh["Average Metadata"][:]
        if is_older:
            d = np.concatenate((d, np.full((d.shape[0],1),-999.0)), axis=1)
        t8 = pd.DataFrame(
            d, columns=["Solar Zenith Angle", "Land Fraction", "Cloud Fraction"]
        )
        tlist.append(t8)

        df = pd.concat(tlist, axis=1)
        fh.close()
        return df


__all__ = ["L1bGeoQaFile"]
