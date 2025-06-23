import geocal  # type: ignore
from ecostress_swig import fill_value_threshold, Resampler, HdfEosFileHandle, HdfEosGrid  # type: ignore
from .l1cg_write_standard_metadata import L1cgWriteStandardMetadata
import os
import h5py
import scipy
import numpy as np
from loguru import logger


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
        l1b_geo,
        l1b_rad,
        output_name,
        inlist,
        local_granule_id=None,
        resolution=70,
        number_subpixel=3,
        run_config=None,
        collection_label="ECOSTRESS",
        build_id="0.30",
        pge_version="0.30",
    ):
        self.l1b_geo = l1b_geo
        self.l1b_rad = l1b_rad
        self.output_name = output_name
        if local_granule_id:
            self.local_granule_id = local_granule_id
        else:
            self.local_granule_id = os.path.basename(output_name)
        self.resolution = resolution
        self.number_subpixel = number_subpixel
        self.run_config = run_config
        self.inlist = inlist
        self.collection_label = collection_label
        self.build_id = build_id
        self.pge_version = pge_version

    def run(self):
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
        fout = HdfEosFileHandle(self.output_name, HdfEosFileHandle.TRUNC)
        g = HdfEosGrid(fout, "ECO_L1CG_RAD_70m", mi)
        g.add_field_uchar("prelim_cloud")
        g.add_field_uchar("water")
        g.add_field_float("view_zenith")
        g.add_field_float("height")
        for i in range(5):
            g.add_field_float(f"data_quality_{i + 1}")
            g.add_field_float(f"radiance_{i + 1}")
        g.close()
        fout.close()
        fout = h5py.File(self.output_name, "r+")
        t = fin_rad["L1B_RADMetadata/CalibrationGainCorrection"][:]
        cal_correction = np.empty((2,t.shape[0]))
        cal_correction[0,:]=t
        cal_correction[1,:]=fin_rad["L1B_RADMetadata/CalibrationOffsetCorrection"][:]
        m = L1cgWriteStandardMetadata(
            fout,
            product_specfic_group="L1CGMetadata",
            proc_lev_desc="Level 1C Gridded Parameters",
            pge_name="L1C",
            collection_label=self.collection_label,
            build_id=self.build_id,
            pge_version=self.pge_version,
            orbit_corrected=fin_geo["L1GEOMetadata/OrbitCorrectionPerformed"][()] == b"True",
            tcorr_before=fin_geo["L1GEOMetadata/DeltaTimeOfCorrectionBeforeScene"][()],
            tcorr_after=fin_geo["L1GEOMetadata/DeltaTimeOfCorrectionAfterScene"][()],
            geolocation_accuracy_qa=fin_geo["L1GEOMetadata/GeolocationAccuracyQA"][()].decode('utf-8'),
            over_all_land_fraction = fin_geo["L1GEOMetadata/OverAllLandFraction"][()],
            average_solar_zenith = fin_geo["L1GEOMetadata/AverageSolarZenith"][()],
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
        m.set("FieldOfViewObstruction", fin_geo["StandardMetadata/FieldOfViewObstruction"][()])
        m.set("ImageLines", mi.number_y_pixel)
        m.set("ImagePixels", mi.number_x_pixel)
        m.set("ImageLineSpacing", self.resolution)
        m.set("ImagePixelSpacing", self.resolution)
        m.set("RangeBeginningDate", fin_geo["StandardMetadata/RangeBeginningDate"][()])
        m.set("RangeBeginningTime", fin_geo["StandardMetadata/RangeBeginningTime"][()])
        m.set("RangeEndingDate", fin_geo["StandardMetadata/RangeEndingDate"][()])
        m.set("RangeEndingTime", fin_geo["StandardMetadata/RangeEndingTime"][()])
        m.set("DayNightFlag",fin_geo["StandardMetadata/DayNightFlag"][()])
        m.set_input_pointer(self.inlist)
        # Not sure if having this open interferes with GDAL, but simple enough to close         
        fin_rad = None 
        dfield = fout["//HDFEOS/GRIDS/ECO_L1CG_RAD_70m/Data Fields"]
        del dfield["prelim_cloud"]
        del dfield["water"]
        del dfield["view_zenith"]
        del dfield["height"]
        for i in range(5):
            del dfield[f"data_quality_{i + 1}"]
            del dfield[f"radiance_{i + 1}"]
        #for b in range(1, 1):
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
        #for b in range(1, 1):
        for b in range(1, 6):
            # GeoCal doesn't support the dqi type. We could update geocal,
            # but no strong reason to. Just read into memory
            logger.info("Doing DQI band %d" % b)
            din = h5py.File(self.l1b_rad)[f"Radiance/data_quality_{b}"][:, :]
            data_in = geocal.MemoryRasterImage(din.shape[0], din.shape[1])
            data_in.write(0, 0, din)
            data = res.resample_dqi(data_in).astype(np.int8)
            t = dfield.create_dataset(
                "data_quality_%d" % b,
                data=data,
                fillvalue=0,
                compression="gzip",
            )
            t.attrs.create("_FillValue", data=0, dtype=t.dtype)
        m.write()

        # TODO Make sure to update bounding box stuff in output metadata
        # TODO Put into place, I think we need to handle this with something
        # other than write_standard_metadata
        # m = self.l1b_geo_generate.m.copy_new_file(
        #    fout, self.local_granule_id, "ECO_L1CG_RAD"
        # )


__all__ = ["L1cgGenerate"]
