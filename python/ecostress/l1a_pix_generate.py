from __future__ import annotations
import geocal  # type: ignore
import h5py  # type: ignore
from .write_standard_metadata import WriteStandardMetadata
from .misc import process_run
from .exception import VicarRunError
import re
import os
import subprocess
import resource
import typing

if typing.TYPE_CHECKING:
    from .run_config import RunConfig


class L1aPixGenerate(object):
    """This generates a L1A pix file from the given L1A_BB and L1A_RAW
    files."""

    def __init__(
        self,
        l1a_bb: str,
        l1a_raw: str,
        l1_osp_dir: str,
        output_name: str,
        output_gain_name: str,
        local_granule_id: str | None = None,
        run_config: None | RunConfig = None,
        build_id: str = "0.30",
        collection_label: str = "ECOSTRESS",
        pge_version: str = "0.30",
        file_version: str = "01",
    ) -> None:
        """Create a L1aPixGenerate with the given input files
        and output file name. To actually generate, execute the 'run'
        command."""
        self.l1a_bb = os.path.abspath(l1a_bb)
        self.l1a_raw = os.path.abspath(l1a_raw)
        self.l1_osp_dir = os.path.abspath(l1_osp_dir)
        self.output_name = output_name
        self.output_gain_name = output_gain_name
        self.local_granule_id = local_granule_id
        self.run_config = run_config
        self.collection_label = collection_label
        self.build_id = build_id
        self.pge_version = pge_version
        self.file_version = file_version

    def _create_dir(self) -> str:
        i = 1
        done = False
        while not done:
            try:
                dirname = "./el1a_run_%03d" % i
                os.makedirs(dirname)
                done = True
            except OSError:
                i += 1
        return dirname

    def run(self) -> None:
        """Do the actual generation of data."""
        # Run Tom's vicar code. Note we assume we are already in the directory
        # to run in, and that Tom's code is on the TAE_PATH. This is try in
        # the way we run with the top level script
        curdir = os.getcwd()
        # The old VICAR programs use a lot of stack space
        # (specifically ibis calls). Linux usually has 8M, we need at
        # least 32M.
        #
        # This usually gets set up in a bashrc or someplace like that,
        # but go ahead and make sure here we have 32M of stack space.
        #
        # Note that VICAR just ends if it runs out of stack space, you
        # don't get any kind of a useful error message.
        #
        # This is the equivalent of "ulimit -s 32768"
        resource.setrlimit(resource.RLIMIT_STACK, (33554432, 33554432))
        try:
            dirname = self._create_dir()
            os.chdir(dirname)
            res = process_run(
                [
                    "vicarb",
                    "el1a_bbcal",
                    "inph5i=%s" % self.l1a_raw,
                    "inph5b=%s" % self.l1a_bb,
                    "inpupf=%s/L1A_PCF_UPF.txt" % self.l1_osp_dir,
                    "pcount=%s" % self.file_version,
                ],
            )
        except subprocess.CalledProcessError:
            raise VicarRunError("VICAR call failed")
        finally:
            os.chdir(curdir)
        # Search through log output for success message, or throw an
        # exception if we don't find it
        mtch = re.search(
            "^VICAR_RESULT-(\d+)-\[(.*)\]", res.decode("utf-8"), re.MULTILINE
        )
        if mtch:
            if mtch.group(1) != "0":
                raise VicarRunError(mtch.group(2))
        else:
            raise VicarRunError("Success result not seen in log")
        fout = h5py.File(self.output_name, "w")
        fout_gain = h5py.File(self.output_gain_name, "w")
        # Copy output from vicar into output file.
        g = fout.create_group("UncalibratedDN")
        for b in range(1, 7):
            t = g.create_dataset(
                "b%d_image" % b,
                data=geocal.mmap_file("%s/UncalibratedDN/b%d_image.hlf" % (dirname, b)),
                compression="gzip",
            )
            t.attrs["Units"] = "dimensionless"
            t.attrs["valid_min"] = 0
            t.attrs["valid_max"] = 32767
        g = fout.create_group("BlackbodyTemp")
        for temp in (325, 295):
            t = g.create_dataset(
                "fpa_%d" % temp,
                data=geocal.mmap_file("%s/BlackbodyTemp/fpa_%d.rel" % (dirname, temp)),
                compression="gzip",
            )
            t.attrs["Units"] = "K"
        g["fpa_325"].attrs["valid_min"] = 310
        g["fpa_325"].attrs["valid_max"] = 330
        g["fpa_295"].attrs["valid_min"] = 275
        g["fpa_295"].attrs["valid_max"] = 305

        g = fout.create_group("BlackbodyBandDN")
        for b in range(1, 7):
            for temp in (325, 295):
                t = g.create_dataset(
                    "b%d_%d" % (b, temp),
                    data=geocal.mmap_file(
                        "%s/BlackBodyDN/dn%db%d.rel" % (dirname, temp, b)
                    ),
                    compression="gzip",
                )
                t.attrs["Units"] = "dimensionless"
                t.attrs["valid_min"] = 0
                t.attrs["valid_max"] = 32767
        g = fout_gain.create_group("Gain")
        g2 = fout_gain.create_group("Offset")
        for b in range(1, 6):
            t = g.create_dataset(
                "b%d_gain" % b,
                data=geocal.mmap_file("%s/ImgRadiance/b%d_gain.rel" % (dirname, b + 1)),
                compression="gzip",
            )
            t.attrs["Units"] = "W/m^2/sr/um"
            t = g2.create_dataset(
                "b%d_offset" % b,
                data=geocal.mmap_file(
                    "%s/ImgRadiance/b%d_offset.rel" % (dirname, b + 1)
                ),
                compression="gzip",
            )
            t.attrs["Units"] = "W/m^2/sr/um"
        g = fout_gain.create_group("SWIR")
        t = g.create_dataset(
            "b6_dcc",
            data=geocal.mmap_file("%s/ImgRadiance/b1_dcc.hlf" % dirname),
            compression="gzip",
        )
        t.attrs["Units"] = "dimensionless"
        # Copy over metadata
        fin = h5py.File(self.l1a_raw, "r")
        g = fout.create_group("Time")
        t = g.create_dataset(
            "line_start_time_j2000", data=fin["Time/line_start_time_j2000"]
        )
        t.attrs["Description"] = "J2000 time of first pixel in line"
        t.attrs["Units"] = "second"
        g = fout.create_group("FPIEencoder")
        t = g.create_dataset("EncoderValue", data=fin["/FPIEencoder/EncoderValue"])
        t.attrs["Description"] = "Mirror encoder value of each focal plane in each scan"
        t.attrs["Units"] = "dimensionless"
        t.attrs["valid_min"] = 0
        t.attrs["valid_max"] = 1749247
        t.attrs["fill"] = 0xFFFFFFFF
        qa_precentage_missing = -999
        if "QAPercentMissingData" in fin["L1A_RAW_PIXMetadata"]:
            qa_precentage_missing = fin["L1A_RAW_PIXMetadata/QAPercentMissingData"][()]
        band_specification = [1.6, 8.2, 8.7, 9.0, 10.5, 12.0]
        if "BandSpecification" in fin["L1A_RAW_PIXMetadata"]:
            band_specification = fin["L1A_RAW_PIXMetadata/BandSpecification"][:]

        m = WriteStandardMetadata(
            fout,
            product_specfic_group="L1A_PIXMetadata",
            proc_lev_desc="Level 1A Calibration Parameters",
            pge_name="L1A_CAL_PGE",
            collection_label=self.collection_label,
            build_id=self.build_id,
            pge_version=self.pge_version,
            local_granule_id=self.local_granule_id,
            qa_precentage_missing=qa_precentage_missing,
            band_specification=band_specification,
        )
        m2 = WriteStandardMetadata(
            fout_gain,
            product_specfic_group="L1A_PIXMetadata",
            proc_lev_desc="Level 1A Calibration Parameters",
            pge_name="L1A_CAL_PGE",
            collection_label=self.collection_label,
            build_id=self.build_id,
            pge_version=self.pge_version,
            local_granule_id=self.local_granule_id,
            qa_precentage_missing=qa_precentage_missing,
            band_specification=band_specification,
        )

        if self.run_config is not None:
            m.process_run_config_metadata(self.run_config)
            m2.process_run_config_metadata(self.run_config)
        m.set("RangeBeginningDate", fin["/StandardMetadata/RangeBeginningDate"][()])
        m.set("RangeBeginningTime", fin["/StandardMetadata/RangeBeginningTime"][()])
        m.set("RangeEndingDate", fin["/StandardMetadata/RangeEndingDate"][()])
        m.set("RangeEndingTime", fin["/StandardMetadata/RangeEndingTime"][()])
        # Short term allow this to fail, just so we can process old data
        # which didn't have FieldOfViewObstruction (added in B7)
        try:
            m.set(
                "FieldOfViewObstruction",
                fin["/StandardMetadata/FieldOfViewObstruction"][()],
            )
        except KeyError:
            pass
        m2.set("RangeBeginningDate", fin["/StandardMetadata/RangeBeginningDate"][()])
        m2.set("RangeBeginningTime", fin["/StandardMetadata/RangeBeginningTime"][()])
        m2.set("RangeEndingDate", fin["/StandardMetadata/RangeEndingDate"][()])
        m2.set("RangeEndingTime", fin["/StandardMetadata/RangeEndingTime"][()])
        # Short term allow this to fail, just so we can process old data
        # which didn't have FieldOfViewObstruction (added in B7)
        try:
            m2.set(
                "FieldOfViewObstruction",
                fin["/StandardMetadata/FieldOfViewObstruction"][()],
            )
        except KeyError:
            pass
        shp = geocal.mmap_file("%s/UncalibratedDN/b1_image.hlf" % dirname).shape
        m.set("ImageLines", shp[0])
        m.set("ImagePixels", shp[1])
        m2.set("ImageLines", shp[0])
        m2.set("ImagePixels", shp[1])
        m.set_input_pointer(
            [self.l1a_raw, self.l1a_bb, "%s/L1A_PCF_UPF.txt" % self.l1_osp_dir]
        )
        m2.set_input_pointer(
            [self.l1a_raw, self.l1a_bb, "%s/L1A_PCF_UPF.txt" % self.l1_osp_dir]
        )
        m.write()
        m2.write()


__all__ = ["L1aPixGenerate"]
