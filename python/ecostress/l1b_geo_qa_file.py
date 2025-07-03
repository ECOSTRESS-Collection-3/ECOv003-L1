from __future__ import annotations
import h5py  # type: ignore
import os
import gzip
import numpy as np
import subprocess
import geocal  # type: ignore
import typing

if typing.TYPE_CHECKING:
    import io
    from .geo_write_standard_metadata import GeoWriteStandardMetadata


class L1bGeoQaFile(object):
    """This is the L1bGeoQaFile. We have a separate class just to make it
    easier to interface with."""

    def __init__(
        self,
        fname: str,
        log_string_handle: io.StringIO,
        local_granule_id: str | None = None,
    ) -> None:
        self.fname = fname
        self.log_string_handle = log_string_handle
        self.scene_name: list[str] | None = None
        self.tp_stat: np.ndarray | None = None
        self.encountered_exception = False
        if local_granule_id:
            self.local_granule_id = local_granule_id
        else:
            self.local_granule_id = os.path.basename(fname)
        # This ends up getting pickled, and h5py doesn't pickle well. So
        # instead of keeping the file open, we reopen and update as needed.

        fout = h5py.File(fname, "w")
        log_group = fout.create_group("Logs")
        log_group.create_group("Tiepoint Logs")
        fout.create_group("Tiepoint")
        fout.create_group("Accuracy Estimate")
        fout.close()

    def write_xml(
        self, igc_initial: str, tpcol: str, igc_sba: str, tpcol_sba: str
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
            g = f.create_group("PythonObject")
            # Note, we compress the data ourselves. While HDF5 supports
            # compression, it doesn't seem to do this with strings.
            for i, fout in enumerate(
                ["igccol_initial", "tpcol", "igccol_sba", "tpcol_sba"]
            ):
                g.create_dataset(fout, data=np.void(gzip.compress(data[i])))
                g.create_dataset(
                    fout + "_desc", data=desc[i], dtype=h5py.special_dtype(vlen=bytes)
                )

    def input_list(self, inlist: list[str]) -> None:
        with h5py.File(self.fname, "a") as f:
            f.create_dataset(
                "Input File List",
                data=[i.encode("utf8") for i in inlist],
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

    def add_orbit(self, orb: geocal.Orbit) -> None:
        """Add data about orbit. Note that this requires we use
        OrbitOffsetCorrection, it doesn't work otherwise."""
        atime, acorr, ptime, pcorr = orb.orbit_correction_parameter()
        with h5py.File(self.fname, "a") as f:
            orb_group = f.create_group("Orbit")
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

    def add_tp_log(self, scene_name: str, tplogfname: str) -> None:
        """Add a TP log file"""
        try:
            log = open(tplogfname, "r").read()
        except FileNotFoundError:
            # Ok if log file isn't found, just given an message
            log = "log file missing"
        with h5py.File(self.fname, "a") as f:
            tplog_group = f["Logs/Tiepoint Logs"]
            tplog_group.create_dataset(
                scene_name, data=log, dtype=h5py.special_dtype(vlen=bytes)
            )

    def add_tp_single_scene(
        self,
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
        if self.tp_stat is None:
            self.tp_stat = np.full((igccol.number_image, 9), -9999.0)
        self.tp_stat[image_index, 0] = ntpoint_initial
        self.tp_stat[image_index, 1] = ntpoint_removed
        self.tp_stat[image_index, 2] = ntpoint_final
        self.tp_stat[image_index, 3] = number_match_try
        if len(tpcol) > 0:
            df = tpcol.data_frame(igccol, image_index)
            self.tp_stat[image_index, 4] = df.ground_2d_distance.quantile(0.68)
        tpdata = None
        if len(tpcol) > 0:
            tpdata = np.empty((len(tpcol), 5))
        for i, tp in enumerate(tpcol):
            ic = tp.image_coordinate(image_index)
            assert tpdata is not None
            tpdata[i, 0:2] = ic.line, ic.sample
            tpdata[i, 2:6] = geocal.Ecr(tp.ground_location).position
        with h5py.File(self.fname, "a") as f:
            tp_group = f["Tiepoint"]
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
        assert self.tp_stat is not None
        self.tp_stat[:, 5] = t
        self.tp_stat[:, 6] = tcor_before
        self.tp_stat[:, 7] = tcor_after
        for i in range(self.tp_stat.shape[0]):
            if geo_qa[i] == "Best":
                self.tp_stat[i, 8] = 0
            elif geo_qa[i] == "Good":
                self.tp_stat[i, 8] = 1
            elif geo_qa[i] == "Suspect":
                self.tp_stat[i, 8] = 2
            elif geo_qa[i] == "Poor":
                self.tp_stat[i, 8] = 3
            else:
                self.tp_stat[i, 8] = -9999

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
            tp_group = f["Tiepoint"]
            tp_group.create_dataset(
                "Scenes", data=self.scene_name, dtype=h5py.special_dtype(vlen=bytes)
            )
            if self.tp_stat is not None:
                dset = tp_group.create_dataset(
                    "Tiepoint Count", data=self.tp_stat[:, 0:4].astype(np.int32)
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
                dset = ac_group.create_dataset(
                    "Accuracy Before Correction", data=self.tp_stat[:, 4]
                )
                dset.attrs["Units"] = "m"
                dset = ac_group.create_dataset(
                    "Final Accuracy", data=self.tp_stat[:, 5]
                )
                dset.attrs["Units"] = "m"
                dset = ac_group.create_dataset(
                    "Delta time correction before scene", data=self.tp_stat[:, 6]
                )
                dset.attrs["Units"] = "s"
                dset = ac_group.create_dataset(
                    "Delta time correction after scene", data=self.tp_stat[:, 7]
                )
                dset.attrs["Units"] = "s"
                dset = ac_group.create_dataset(
                    "Geolocation accuracy QA flag", data=self.tp_stat[:, 8]
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


__all__ = ["L1bGeoQaFile"]
