from __future__ import annotations
import numpy as np
import os
import re
import copy
import typing
from pathlib import Path
from typing import Any
from typing_extensions import Self

if typing.TYPE_CHECKING:
    import h5py  # type: ignore
    from .run_config import RunConfig


class WriteStandardMetadata(object):
    """This writes the standard metadata"""

    def __init__(
        self,
        hdf_file: h5py.File | None,
        product_specfic_group: str = "L1GEOMetadata",
        proc_lev_desc: str = "Level 1 Geolocation Parameters",
        pge_name: str = "L1B_GEO",
        xml_file: str | os.PathLike[str] | None = None,
        json_file: str | os.PathLike[str] | None = None,
        local_granule_id: str | None = None,
        collection_label: str = "ECOSTRESS",
        build_id: str = "0.01",
        pge_version: str = "0.01",
        qa_precentage_missing: None | float = None,
        band_specification: None | list[float] = None,
        orbit_based: bool = False,
        level0_file: bool = False,
        hdfeos_file: bool = False,
    ) -> None:
        """hdf_file should be the h5py.File handler. You can pass the
        local_granule_id, or if None we assume the filename for the hdf_file is
        the local_granule_id"""
        self.hdf_file = hdf_file
        self.xml_file = Path(xml_file) if xml_file is not None else None
        self.json_file = Path(json_file) if json_file is not None else None
        self.orbit_based = orbit_based
        self.product_specfic_group = product_specfic_group
        self.hdfeos_file = hdfeos_file
        if local_granule_id is None:
            if hdf_file is not None:
                local_granule_id = os.path.basename(hdf_file.filename)
            else:
                if self.xml_file is None:
                    raise RuntimeError("Need to supply either hdf_file or xml_file")
                local_granule_id = self.xml_file.stem
        self.local_granule_id = local_granule_id

        # Initialize all the data.
        self.data: dict[str, Any] = {}
        for k, typ in self.mlist:
            if typ == "String":
                self.data[k] = "dummy"
            elif typ == "StringorNone":
                self.data[k] = None
            elif typ == "Float64":
                self.data[k] = np.float64(0.0)
            elif typ == "Float64orNone":
                self.data[k] = None
            elif typ == "Int32":
                self.data[k] = np.int32(0)
            elif typ == "Float32":
                self.data[k] = np.float32(0.0)
            else:
                raise RuntimeError("Unrecognized type '%s'" % typ)
        # Fill in values we can.
        self.set("AncillaryInputPointer", product_specfic_group)
        self.set("AutomaticQualityFlag", "PASS")
        self.set("CampaignShortName", "Primary")
        self.set("DataFormatType", "NCSAHDF5")
        # How do we determine these?
        self.set("HDFVersionID", "1.8.16")
        self.set("ImageLines", 5400)
        self.set("ImageLineSpacing", 68.754)
        self.set("ImagePixels", 5400)
        self.set("ImagePixelSpacing", 65.536)

        self.set("InstrumentShortName", "ECOSTRESS")
        self.set("LongName", "ECOSTRESS")
        self.set("PGEName", pge_name)
        self.set("PlatformLongName", "ISS")
        self.set("PlatformShortName", "ISS")
        self.set("PlatformType", "Spacecraft")
        self.set("ProcessingLevelDescription", proc_lev_desc)
        self.set("ProducerAgency", "JPL")
        self.set("ProducerInstitution", "Caltech")
        self.set("CampaignShortName", "Primary")
        self.set("RegionID", "")
        self.set("DayNightFlag", "NA")
        self.set("SISName", "Level 1 Product Specification Document (JPL D-94634)")
        self.set("SISVersion", "Preliminary")
        self.set("BuildID", build_id)
        self.set("CollectionLabel", collection_label)
        self.set("PGEVersion", pge_version)
        self.set("LocalGranuleID", local_granule_id)
        self.qa_precentage_missing = qa_precentage_missing
        self.band_specification = band_specification
        # For now parse the local granule id to get some of the metadata.
        # Might get this from the run config file instead
        if level0_file:
            # Can't set the next bit, so skip it
            return
        elif orbit_based:
            m = re.match(
                r"(ECO[^_]*_)?(?P<process_level>\w+)_(\w+)_(?P<orbit>\d{5})_",
                local_granule_id,
            )
        else:
            m = re.match(
                r"(ECO[^_]*_)?(?P<process_level>\w+)_(\w+)_(?P<orbit>\d{5})_(?P<scene_id>\d{3})",
                local_granule_id,
            )
        if not m:
            raise RuntimeError("Unrecognized local granule id '%s'" % local_granule_id)
        self.set("StartOrbitNumber", m.group("orbit"))
        self.set("StopOrbitNumber", m.group("orbit"))
        if orbit_based:
            self.set("SceneID", "NA")
            self.set("FieldOfViewObstruction", "NA")
        else:
            self.set("SceneID", m.group("scene_id"))
        self.set("ProcessingLevelID", m.group("process_level"))

    def set_input_pointer(self, flist: list[str]) -> None:
        """Take a list of file names, and generates the InputPointer from this"""
        self.set("InputPointer", ",".join(os.path.basename(i) for i in flist))

    def set(self, m: str, v: Any) -> None:
        if m not in self.data:
            raise RuntimeError(f"Key '{m}' is not in standard metadata")
        if isinstance(self.data[m], bytes) or isinstance(self.data[m], str):
            self.data[m] = v
        elif isinstance(self.data[m], np.float64):
            self.data[m] = np.float64(v)
        elif isinstance(self.data[m], np.int32):
            self.data[m] = np.int32(v)
        elif isinstance(self.data[m], np.float32):
            self.data[m] = np.float32(v)
        elif self.data[m] is None:
            self.data[m] = v
        else:
            raise RuntimeError("Unrecognized type")

    def pad_string(self, s: bytes, ln: int) -> np.bytes_:
        """Create a fixed length string. Note not currently used, but we'll
        leave the function here in case we end up needing it."""
        if len(s) > ln:
            raise RuntimeError(
                "String '%s' is longer than allowed size %d" % (s.decode("utf-8"), ln)
            )
        if len(s) == ln:
            return np.bytes_(s)
        return np.bytes_(s + b"\0" * (ln - len(s)))

    @property
    def mlist(self) -> list[tuple[str, str]]:
        return [
            ("AncillaryInputPointer", "String"),
            ("AutomaticQualityFlag", "String"),
            ("BuildID", "String"),
            ("CollectionLabel", "String"),
            ("CloudCover", "Float64orNone"),
            ("GeolocationAccuracyQA", "StringorNone"),
            ("GeolocationAccuracyQAExplanation", "StringorNone"),
            ("DataFormatType", "String"),
            ("DayNightFlag", "String"),
            ("EastBoundingCoordinate", "Float64"),
            ("HDFVersionID", "String"),
            ("ImageLines", "Int32"),
            ("ImageLineSpacing", "Float32"),
            ("ImagePixels", "Int32"),
            ("ImagePixelSpacing", "Float32"),
            ("InputPointer", "String"),
            ("InstrumentShortName", "String"),
            ("LocalGranuleID", "String"),
            ("LongName", "String"),
            ("NorthBoundingCoordinate", "Float64"),
            ("PGEName", "String"),
            ("PGEVersion", "String"),
            ("PlatformLongName", "String"),
            ("PlatformShortName", "String"),
            ("PlatformType", "String"),
            ("ProcessingLevelID", "String"),
            ("ProcessingLevelDescription", "String"),
            ("ProducerAgency", "String"),
            ("ProducerInstitution", "String"),
            ("ProductionDateTime", "String"),
            ("ProductionLocation", "String"),
            ("CampaignShortName", "String"),
            ("RangeBeginningDate", "String"),
            ("RangeBeginningTime", "String"),
            ("RangeEndingDate", "String"),
            ("RangeEndingTime", "String"),
            ("RegionID", "String"),
            ("SceneID", "String"),
            ("ShortName", "String"),
            ("SISName", "String"),
            ("SISVersion", "String"),
            ("SouthBoundingCoordinate", "Float64"),
            ("StartOrbitNumber", "String"),
            ("StopOrbitNumber", "String"),
            ("WestBoundingCoordinate", "Float64"),
            ("FieldOfViewObstruction", "String"),
        ]

    def clear_old(self, g: h5py.Group) -> None:
        """Clear any old metadata fields."""
        for m, typ in self.mlist:
            if m in g:
                del g[m]

    def process_run_config_metadata(self, run_config: RunConfig) -> None:
        """This takes a RunConfig object is fills in the metadata we can
        from this file."""
        self.data["ShortName"] = run_config["ProductPathGroup", "ShortName"]
        self.data["ProductionDateTime"] = run_config[
            "JobIdentification", "ProductionDateTime"
        ]
        self.data["ProductionLocation"] = run_config[
            "JobIdentification", "ProductionLocation"
        ]

    def copy_new_file(
        self, hdf_file: h5py.File, local_granule_id: str, short_name: str
    ) -> Self:
        """Copy metadata, applying to a different file"""
        h = self.hdf_file
        self.hdf_file = None
        mcopy = copy.deepcopy(self)
        self.hdf_file = h
        mcopy.hdf_file = hdf_file
        mcopy.local_granule_id = local_granule_id
        mcopy.set("LocalGranuleID", local_granule_id)
        mcopy.set("ShortName", short_name)
        return mcopy

    def write_xml(self) -> None:
        if self.xml_file is None:
            raise RuntimeError("Need to have xml_file to call write_xml")
        fh = open(self.xml_file, "w")
        # Not sure what the significance of the xmls is here, but this comes
        # from Gregories' code (see ECOSTRESS-Collection-2/ECOSTRESS/XML_metadata.py)
        print(
            """<?xml version="1.0" encoding="UTF-8"?>
<cas:metadata xmlns:cas="http://oodt.jpl.nasa.gov/1.0/cas">""",
            file=fh,
        )
        klist = sorted([m for m, _ in self.mlist])
        for m in klist:
            if self.data[m] is not None:
                val = self.data[m]
                if hasattr(val, "decode"):
                    val = val.decode("utf-8")
                print(
                    f"""   <keyval type="vector">
      <key>{m}</key>
      <val>{val}</val>
   </keyval>""",
                    file=fh,
                )
        print("</cas:metadata>", file=fh)
        fh.close()

    def write(self) -> None:
        """Actually write the metadata."""
        if self.xml_file is not None:
            self.write_xml()
        if self.hdf_file is None:
            if self.xml_file is not None:
                return
            raise RuntimeError("Need either hdf_file or xml_file to write")
        gname = "StandardMetadata"
        if self.hdfeos_file:
            gname = "/HDFEOS/ADDITIONAL/FILE_ATTRIBUTES/StandardMetadata"
        if gname in self.hdf_file:
            g = self.hdf_file[gname]
        else:
            g = self.hdf_file.create_group(gname)
        self.clear_old(g)
        for m, typ in self.mlist:
            if self.data[m] is not None:
                g[m] = self.data[m]
        pgname = self.product_specfic_group
        if self.hdfeos_file:
            pgname = f"/HDFEOS/ADDITIONAL/FILE_ATTRIBUTES/{self.product_specfic_group}"
        if pgname in self.hdf_file:
            pg = self.hdf_file[pgname]
        else:
            pg = self.hdf_file.create_group(pgname)
        pg["AncillaryFiles"] = np.int32(0)
        if self.qa_precentage_missing is not None:
            pg["QAPercentMissingData"] = np.float32(self.qa_precentage_missing)
            pg["QAPercentMissingData"].attrs["Units"] = "percentage"
            pg["QAPercentMissingData"].attrs["valid_min"] = 0
            pg["QAPercentMissingData"].attrs["valid_max"] = 100
        if self.band_specification is not None:
            pg.create_dataset(
                "BandSpecification", data=self.band_specification, dtype=np.float32
            )
            pg["BandSpecification"].attrs["Units"] = "micrometer"
            pg["BandSpecification"].attrs["valid_min"] = 1.6
            pg["BandSpecification"].attrs["valid_max"] = 12.1
            pg["BandSpecification"].attrs["fill"] = 0
