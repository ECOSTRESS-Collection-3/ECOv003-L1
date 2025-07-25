from __future__ import annotations
import geocal  # type: ignore
from ecostress_swig import FILL_VALUE_NOT_SEEN, Resampler, fill_value_threshold  # type: ignore
from .misc import determine_rotated_map_igc
import os
import h5py  # type: ignore
import numpy as np
import scipy  # type: ignore
import subprocess
from loguru import logger
import typing

if typing.TYPE_CHECKING:
    from .l1b_geo_generate import L1bGeoGenerate


class L1bGeoGenerateMap(object):
    """This generates a L1B Geo map product. Right now we leverage off of
    the L1bGeoGenerate class, since most of the work is the same. We could
    break this connection if it is ever needed, but at least currently
    we always generate the L1bGeoGenerate and optionally do the
    L1bGeoGenerateMap.

    Like L1bGeoGenerate, to actually generate you should execute the "run"
    command. Make sure the L1bGeoGenerate run has been executed first, we rely
    on data generated there.

    By default, we generate a rotated map. You can instead force a north is up
    map by setting north_up to true. Likewise, default resolution is 70 meters,
    but you can modify this.
    """

    def __init__(
        self,
        l1b_geo_generate: L1bGeoGenerate,
        l1b_rad: str,
        output_name: str,
        local_granule_id: str | None = None,
        resolution: float = 70,
        north_up: bool = False,
        number_subpixel: int = 3,
    ) -> None:
        self.l1b_geo_generate = l1b_geo_generate
        self.l1b_rad = l1b_rad
        self.output_name = output_name
        if local_granule_id:
            self.local_granule_id = local_granule_id
        else:
            self.local_granule_id = os.path.basename(output_name)
        self.north_up = north_up
        self.resolution = resolution
        self.number_subpixel = number_subpixel

    def run(self) -> None:
        fout = h5py.File(self.output_name, "w")
        m = self.l1b_geo_generate.m.copy_new_file(
            fout, self.local_granule_id, "ECO1BMAPRAD"
        )
        fin = h5py.File(self.l1b_rad, "r")
        m.qa_precentage_missing = -999
        if "QAPercentMissingData" in fin["L1B_RADMetadata"]:
            m.qa_precentage_missing = fin["L1B_RADMetadata/QAPercentMissingData"][()]
        m.band_specification = [1.6, 8.2, 8.7, 9.0, 10.5, 12.0]
        if "BandSpecification" in fin["L1B_RADMetadata"]:
            m.band_specification = fin["L1B_RADMetadata/BandSpecification"][:]
        m.write()
        mi = geocal.cib01_mapinfo(self.resolution)
        # Most of the time, we have no fill values so just do a normal zoom
        if (
            np.count_nonzero(self.l1b_geo_generate.lat < fill_value_threshold) == 0
            and np.count_nonzero(self.l1b_geo_generate.lon < fill_value_threshold) == 0
        ):
            lat = scipy.ndimage.interpolation.zoom(
                self.l1b_geo_generate.lat, self.number_subpixel, order=2
            )
            lon = scipy.ndimage.interpolation.zoom(
                self.l1b_geo_generate.lon, self.number_subpixel, order=2
            )
        else:
            # But if we do, have special handling
            #
            # Order here of "1" is bilinear. We can't use higher order since we
            # may have missing data and this gets spread out with higher order
            # interpolation. As an easy way of handling this, we set
            # missing data as extremely negative value
            latv = self.l1b_geo_generate.lat.copy()
            lonv = self.l1b_geo_generate.lon.copy()
            latv[latv < fill_value_threshold] = -1e20
            lonv[lonv < fill_value_threshold] = -1e20
            lat = scipy.ndimage.interpolation.zoom(
                self.l1b_geo_generate.lat, self.number_subpixel, order=1
            )
            lon = scipy.ndimage.interpolation.zoom(
                self.l1b_geo_generate.lon, self.number_subpixel, order=1
            )
        if not self.north_up:
            mi = determine_rotated_map_igc(self.l1b_geo_generate.igc, mi)
        res = Resampler(lon, lat, mi, self.number_subpixel, False)
        logger.info("Done with Resampler init")
        g = fout.create_group("Mapped")
        g2 = g.create_group("MapInformation")
        g2["README"] = """We specify the Map Information by giving the Coordinate System
and a Affine GeoTransform. The Coordinate System is specified as 
OpeGIS Well Known Text strings(see for example
https://en.wikipedia.org/wiki/Well-known_text or 
http://www.gdal.org/gdal_datamodel.html). This is given in the
CoordinateSystem.

We also specify the Affine GeoTransform (as for example in
geotiff, see http://geotiff.maptools.org/spec/geotiff2.6.html or
GDAL, see http://www.gdal.org/gdal_datamodel.html). This is given
in the GeoTransform. We have:

longitude   = GT_0 + GT_1 * i + GT_2 * j
latitude    = GT_3 + GT_4 * i + GT_5 * j

Where (i,j) is the sample, line of the pixel (starting at 0) and longitude
and latitude are given in degrees.

Note that in addition, we have the latitude and longitude fields in
the file. This is completely redundant with the map projection information,
we supply these fields as a convenience for software that expects this
data. But you can directly calculate latitude and longitude from the map
information.
"""
        # Hardcoded for now, this is probably fine since we don't expect to
        # change the coordinate system
        g2["CoordinateSystem"] = """GEOGCS["WGS 84",
    DATUM["WGS_1984",
        SPHEROID["WGS 84",6378137,298.257223563,
            AUTHORITY["EPSG","7030"]],
        AUTHORITY["EPSG","6326"]],
    PRIMEM["Greenwich",0],
    UNIT["degree",0.0174532925199433],
    AUTHORITY["EPSG","4326"]]
"""
        g2.create_dataset("GeoTransform", data=res.map_info.transform, dtype="f8")
        lat, lon, height = res.map_values(self.l1b_geo_generate.igc.dem)
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
        logger.info("Done with lat, lon, height")
        # Land fraction
        for b in range(1, 6):
            logger.info("Doing band %d" % b)
            data_in = geocal.GdalRasterImage(
                'HDF5:"%s"://Radiance/radiance_%d' % (self.l1b_rad, b)
            )
            data = res.resample_field(data_in, 1.0, False, FILL_VALUE_NOT_SEEN).astype(
                np.float32
            )
            t = g.create_dataset(
                "radiance_%d" % b,
                data=data,
                dtype="f4",
                fillvalue=FILL_VALUE_NOT_SEEN,
                compression="gzip",
            )
            t.attrs.create("_FillValue", data=FILL_VALUE_NOT_SEEN, dtype=t.dtype)
            t.attrs["Units"] = "W/m^2/sr/um"
            data_in = geocal.GdalRasterImage(
                'HDF5:"%s"://Radiance/data_quality_%d' % (self.l1b_rad, b)
            )
            data = res.resample_dqi(data_in).astype(np.int8)
            t = g.create_dataset("data_quality_%d" % b, data=data, compression="gzip")
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
      instrument design instead of some problem.
"""
            t.attrs["Units"] = "dimensionless"

        logger.info("Doing SWIR")
        data_in = geocal.GdalRasterImage('HDF5:"%s"://SWIR/swir_dn' % self.l1b_rad)
        data = res.resample_field(data_in, 1.0, False, FILL_VALUE_NOT_SEEN).astype(
            np.int16
        )
        t = g.create_dataset(
            "swir_dn", data=data, fillvalue=FILL_VALUE_NOT_SEEN, compression="gzip"
        )
        t.attrs.create("_FillValue", data=FILL_VALUE_NOT_SEEN, dtype=t.dtype)
        t.attrs["Units"] = "dimensionless"
        for fld in ["solar_azimuth", "solar_zenith", "view_azimuth", "view_zenith"]:
            logger.info("Doing %s" % fld)
            data_in = geocal.GdalRasterImage(
                'HDF5:"%s"://Geolocation/%s' % (self.l1b_geo_generate.output_name, fld)
            )
            data = res.resample_field(
                data_in, 1.0, False, FILL_VALUE_NOT_SEEN, True
            ).astype(np.float32)
            t = g.create_dataset(
                fld,
                data=data,
                dtype="f4",
                fillvalue=FILL_VALUE_NOT_SEEN,
                compression="gzip",
            )
            t.attrs.create("_FillValue", data=FILL_VALUE_NOT_SEEN, dtype=t.dtype)
            t.attrs["Units"] = "degrees"
            t.attrs["Description"] = (
                """%s field. Note that a ground location is in general seen multiple
times. It doesn't make sense to average the data like we do for radiance.
Instead, we give the angle for the ECOSTRESS image coordinate that has the
smallest line and sample number."""
                % fld
            )
        g["solar_azimuth"].attrs["valid_min"] = -180
        g["solar_azimuth"].attrs["valid_max"] = 180
        g["view_azimuth"].attrs["valid_min"] = -180
        g["view_azimuth"].attrs["valid_max"] = 180
        g["solar_zenith"].attrs["valid_min"] = -90
        g["solar_zenith"].attrs["valid_max"] = 90
        g["view_zenith"].attrs["valid_min"] = -90
        g["view_zenith"].attrs["valid_max"] = 90
        fout.close()
        vrtfile = os.path.splitext(self.output_name)[0] + "_gdal.vrt"
        cmd = ["gdalbuildvrt", "-separate", vrtfile]
        cmd.extend(
            'HDF5:"%s"://Mapped/radiance_%d' % (self.output_name, b + 1)
            for b in range(5)
        )
        cmd.append('HDF5:"%s"://Mapped/swir_dn' % self.output_name)
        cmd.append('HDF5:"%s"://Mapped/data_quality_1' % self.output_name)
        cmd.append('HDF5:"%s"://Mapped/data_quality_2' % self.output_name)
        cmd.append('HDF5:"%s"://Mapped/data_quality_3' % self.output_name)
        cmd.append('HDF5:"%s"://Mapped/data_quality_4' % self.output_name)
        cmd.append('HDF5:"%s"://Mapped/data_quality_5' % self.output_name)
        cmd.append('HDF5:"%s"://Mapped/latitude' % self.output_name)
        cmd.append('HDF5:"%s"://Mapped/longitude' % self.output_name)
        cmd.append('HDF5:"%s"://Mapped/height' % self.output_name)
        cmd.append('HDF5:"%s"://Mapped/solar_azimuth' % self.output_name)
        cmd.append('HDF5:"%s"://Mapped/solar_zenith' % self.output_name)
        cmd.append('HDF5:"%s"://Mapped/view_azimuth' % self.output_name)
        cmd.append('HDF5:"%s"://Mapped/view_zenith' % self.output_name)
        subprocess.run(cmd)
        tstring = ",".join("{:.20e}".format(t) for t in res.map_info.transform)
        cmd = [
            "sed",
            "-i",
            's#</SRS>#</SRS>\\n  <GeoTransform>%s</GeoTransform>\\n  <Metadata>\\n    <MDI key="AREA_OR_POINT">Area</MDI>\\n  </Metadata>#'
            % tstring,
            vrtfile,
        ]
        subprocess.run(cmd)
        with open(
            os.path.splitext(self.output_name)[0] + "_gdal_README.txt", "w"
        ) as fh:
            print("Band 1 - Radiance 1 (8.28 micron)", file=fh)
            print("Band 2 - Radiance 2 (8.63 micron)", file=fh)
            print("Band 3 - Radiance 3 (9.07 micron)", file=fh)
            print("Band 4 - Radiance 4 (10.52 micron)", file=fh)
            print("Band 5 - Radiance 5 (12.05 micron)", file=fh)
            print("Band 6 - SWIR DN (1.62 micron)", file=fh)
            print("Band 7 - Data quality band 1", file=fh)
            print("Band 8 - Data quality band 2", file=fh)
            print("Band 9 - Data quality band 3", file=fh)
            print("Band 10 - Data quality band 4", file=fh)
            print("Band 11 - Data quality band 5", file=fh)
            print("Band 12 - Latitude", file=fh)
            print("Band 13 - Longitude", file=fh)
            print("Band 14 - Height", file=fh)
            print("Band 16 - Solar Azimuth", file=fh)
            print("Band 17 - Solar Zenith", file=fh)
            print("Band 18 - View Azimuth", file=fh)
            print("Band 19 - View Zenith", file=fh)


__all__ = ["L1bGeoGenerateMap"]
