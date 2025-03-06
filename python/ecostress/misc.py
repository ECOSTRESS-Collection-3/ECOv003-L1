# This is various miscellaneous routines that don't fit elsewhere
import geocal  # type: ignore
import re
import subprocess
import h5py  # type: ignore
import os
import sys
import math
import glob
import numpy as np
from ecostress_swig import (  # type: ignore
    EcostressScanMirror,
    EcostressTimeTable,
    EcostressOrbit,
    EcostressOrbitL0Fix,
    EcostressImageGroundConnection,
    EcostressIgcCollection,
)
import pickle

orb_to_date = None


def orb_to_path(orbnum):
    global orb_to_date
    if orb_to_date is None:
        orb_to_date = pickle.load(
            open("/project/sandbox/smyth/orbit_to_date.pkl", "rb")
        )
    if int(orbnum) not in orb_to_date:
        raise RuntimeError(
            f"Orbit {orbnum} not found. Do you need to run orbit_to_date.py?"
        )
    return orb_to_date[int(orbnum)]


def find_radiance_file(orbnum, scene, multiple_ok=False):
    """Simple function to find a radiance file by orbit number and scene.
    Note that this is a pretty simplistic function, and doesn't handle things
    like multiple versions etc. But I need to simple functionality often
    enough that it is worth havings."""
    f = glob.glob(
        f"/ops/store*/PRODUCTS/L1B_RAD/{orb_to_path(orbnum)[0]}/ECOSTRESS_L1B_RAD_%05d_%03d_*.h5"
        % (int(orbnum), int(scene))
    )
    if len(f) == 0:
        f = glob.glob(
            f"/ops/store*/PRODUCTS/L1B_RAD/{orb_to_path(orbnum)[1]}/ECOSTRESS_L1B_RAD_%05d_%03d_*.h5"
            % (int(orbnum), int(scene))
        )
    if len(f) == 0:
        raise RuntimeError(f"Radiance file for {orbnum}, scene {scene} not found")
    if len(f) > 1 and not multiple_ok:
        raise RuntimeError(f"Multiple radiance files found for {orbnum}, scene {scene}")
    return f[0]


def find_orbit_file(orbnum, raw_att=False, multiple_ok=False):
    """Simple function to find a orbit file by orbit number and scene.
    Note that this is a pretty simplistic function, and doesn't handle things
    like multiple versions etc. But I need to simple functionality often
    enough that it is worth havings.

    By default this finds the corrected orbit (ECOSTRESS_L1B_ATT), but you can
    optionally request a raw file before correction (L1A_RAW_ATT)"""
    if raw_att:
        f = glob.glob(
            f"/ops/store*/PRODUCTS/L1A_RAW_ATT/{orb_to_path(orbnum)[0]}/L1A_RAW_ATT_%05d_*.h5"
            % int(orbnum)
        )
    else:
        f = glob.glob(
            f"/ops/store*/PRODUCTS/L1B_ATT/{orb_to_path(orbnum)[0]}/ECOSTRESS_L1B_ATT_%05d_*.h5"
            % int(orbnum)
        )
    if len(f) == 0:
        raise RuntimeError(f"Orbit file for {orbnum} not found")
    if len(f) > 1 and not multiple_ok:
        raise RuntimeError(f"Multiple orbit files found for {orbnum}")
    return f[0]


def create_igc(rad_fname, orb_fname, l1_osp_dir=None, dem=None, title=""):
    """Create a IGC for the given radiance and orbit file.

    The DEM can be passed in, but if it isn't then we use the default
    locations for everything (e.g, read ELEV_ROOT environment variable)."""
    if l1_osp_dir is None:
        if "L1_OSP_DIR" not in os.environ:
            raise RuntimeError(
                "Need to either set L1_OSP_DIR environment variable, or pass the directory in."
            )
        l1_osp_dir = os.environ["L1_OSP_DIR"]
    sys.path.append(l1_osp_dir)
    try:
        import l1b_geo_config  # type: ignore

        if (
            hasattr(l1b_geo_config, "fix_l0_time_tag")
            and l1b_geo_config.fix_l0_time_tag
        ):
            orb = EcostressOrbitL0Fix(
                orb_fname,
                l1b_geo_config.x_offset_iss,
                l1b_geo_config.extrapolation_pad,
                l1b_geo_config.large_gap,
            )
        else:
            orb = EcostressOrbit(
                orb_fname,
                l1b_geo_config.x_offset_iss,
                l1b_geo_config.extrapolation_pad,
                l1b_geo_config.large_gap,
            )
        cam = geocal.read_shelve(f"{l1_osp_dir}/camera.xml")
        if dem is None:
            dem = geocal.SrtmDem("", False)
        tt = create_time_table(
            rad_fname, l1b_geo_config.mirror_rpm, l1b_geo_config.frame_time
        )
        sm = create_scan_mirror(
            rad_fname,
            l1b_geo_config.max_encoder_value,
            l1b_geo_config.first_encoder_value_0,
            l1b_geo_config.second_encoder_value_0,
            l1b_geo_config.instrument_to_sc_euler,
            l1b_geo_config.first_angle_per_encoder_value,
            l1b_geo_config.second_angle_per_encoder_value,
        )
        line_order_reversed = False
        if (
            as_string(
                h5py.File(rad_fname, "r")["/L1B_RADMetadata/RadScanLineOrder"][()]
            )
            == "Reverse line order"
        ):
            line_order_reversed = True
        cam.line_order_reversed = line_order_reversed
        cam.focal_length = l1b_geo_config.camera_focal_length
        is_day = (
            as_string(h5py.File(rad_fname, "r")["StandardMetadata/DayNightFlag"][()])
            == "Day"
        )
        b = (
            l1b_geo_config.ecostress_day_band
            if is_day
            else l1b_geo_config.ecostress_night_band
        )
        ras = geocal.GdalRasterImage(
            'HDF5:"%s"://Radiance/radiance_%d' % (rad_fname, b)
        )
        ras = geocal.ScaleImage(ras, 100.0)
        igc = EcostressImageGroundConnection(orb, tt, cam, sm, dem, ras, title)
        return igc
    finally:
        sys.path.pop()


def create_igccol(
    orbnum, scene, l1_osp_dir=None, dem=None, title="", multiple_ok=False
):
    """Variation of create_igc that puts the IGC as a single entry in
    an IgcCollection (which has support for parameters). This finds the
    radiance and orbit data for the given orbit and scene number."""
    igccol = EcostressIgcCollection()
    igccol.add_igc(
        create_igc(
            find_radiance_file(orbnum, scene, multiple_ok=multiple_ok),
            find_orbit_file(orbnum, multiple_ok=multiple_ok),
            l1_osp_dir=l1_osp_dir,
            dem=dem,
            title=title,
        )
    )
    return igccol


def create_igccol_from_qa(qa_fname, l1_osp_dir=None, dem=None, raw_att=False):
    """Create a IgcCollection from a given qa file, using the same input files as it has
    listed. By default we use the corrected llb_att file, but you can optionally select the
    raw l1a_raw_att file.  We add the attribute "scene_list" to the igccol for convenience."""
    if l1_osp_dir is None:
        if "L1_OSP_DIR" not in os.environ:
            raise RuntimeError(
                "Need to either set L1_OSP_DIR environment variable, or pass the directory in."
            )
        l1_osp_dir = os.environ["L1_OSP_DIR"]

    f = h5py.File(qa_fname, "r")
    t = f["StandardMetadata/InputPointer"][()].decode("utf-8").split(",")
    radlist = [
        fname for fname in t if re.match(r"ECOSTRESS_L1B_RAD|ECOv002_L1B_RAD", fname)
    ]
    l1a_att_fname = [fname for fname in t if re.match(r"L1A_RAW_ATT", fname)][0]
    m = re.match(r"L1B_GEO_QA_(\d{5})_(\d{8})T\d+_(.*\.h5)", os.path.basename(qa_fname))
    if not m:
        raise RuntimeError(f"Don't recognize QA file name {qa_fname}")
    orbnum = int(m[1])
    qa_fstem = m[3]
    datelist = set()
    for fname in radlist:
        m = re.match(
            r"(ECOSTRESS_L1B_RAD|ECOv002_L1B_RAD)_(\d{5})_\d{3}_(\d{8})T\d+_(.*\.h5)",
            fname,
        )
        if not m:
            raise RuntimeError(f"Don't recognize file name {fname}")
        fbase = m[1]
        orbnum = int(m[2])
        datelist.add(f"{m[3][:4]}/{m[3][4:6]}/{m[3][6:]}")
    flist = []
    for d in datelist:
        flist.extend(
            glob.glob(f"/ops/store*/PRODUCTS/L1B_RAD/{d}/{fbase}_{orbnum:05d}_*.h5")
        )
    # Might be extra files found on the system not used in the run
    radlist = [fname for fname in flist if os.path.basename(fname) in radlist]

    def scene_from_fname(fname):
        m = re.match(
            r"(ECOSTRESS_L1B_RAD|ECOv002_L1B_RAD)_\d{5}_(\d{3})",
            os.path.basename(fname),
        )
        return int(m[2])

    radlist.sort(key=scene_from_fname)
    scene_list = [scene_from_fname(fname) for fname in radlist]
    flist = []
    for d in datelist:
        flist.extend(glob.glob(f"/ops/store*/PRODUCTS/L1A_RAW_ATT/{d}/{l1a_att_fname}"))
    l1a_att_fname = flist[0]
    flist = []
    for d in datelist:
        flist.extend(
            glob.glob(f"/ops/store*/PRODUCTS/L1B_ATT/{d}/*_{orbnum:05d}_*_{qa_fstem}")
        )
    l1b_att_fname = flist[0]
    orb_fname = l1a_att_fname if raw_att else l1b_att_fname
    try:
        sys.path.append(l1_osp_dir)
        import l1b_geo_config

        if (
            hasattr(l1b_geo_config, "fix_l0_time_tag")
            and l1b_geo_config.fix_l0_time_tag
        ):
            orb = EcostressOrbitL0Fix(
                orb_fname,
                l1b_geo_config.x_offset_iss,
                l1b_geo_config.extrapolation_pad,
                l1b_geo_config.large_gap,
            )
        else:
            orb = EcostressOrbit(
                orb_fname,
                l1b_geo_config.x_offset_iss,
                l1b_geo_config.extrapolation_pad,
                l1b_geo_config.large_gap,
            )
        cam = geocal.read_shelve(f"{l1_osp_dir}/camera.xml")
        if dem is None:
            dem = geocal.SrtmDem("", False)
        igccol = EcostressIgcCollection()
        for rad_fname, scene in zip(radlist, scene_list):
            tt = create_time_table(
                rad_fname, l1b_geo_config.mirror_rpm, l1b_geo_config.frame_time
            )
            sm = create_scan_mirror(
                rad_fname,
                l1b_geo_config.max_encoder_value,
                l1b_geo_config.first_encoder_value_0,
                l1b_geo_config.second_encoder_value_0,
                l1b_geo_config.instrument_to_sc_euler,
                l1b_geo_config.first_angle_per_encoder_value,
                l1b_geo_config.second_angle_per_encoder_value,
            )
            line_order_reversed = False
            if (
                as_string(
                    h5py.File(rad_fname, "r")["/L1B_RADMetadata/RadScanLineOrder"][()]
                )
                == "Reverse line order"
            ):
                line_order_reversed = True
            cam.line_order_reversed = line_order_reversed
            cam.focal_length = l1b_geo_config.camera_focal_length
            is_day = (
                as_string(
                    h5py.File(rad_fname, "r")["StandardMetadata/DayNightFlag"][()]
                )
                == "Day"
            )
            b = (
                l1b_geo_config.ecostress_day_band
                if is_day
                else l1b_geo_config.ecostress_night_band
            )
            ras = geocal.GdalRasterImage(
                'HDF5:"%s"://Radiance/radiance_%d' % (rad_fname, b)
            )
            ras = geocal.ScaleImage(ras, 100.0)
            igccol.add_igc(
                EcostressImageGroundConnection(
                    orb, tt, cam, sm, dem, ras, f"Scene {scene}"
                )
            )
        igccol.scene_list = scene_list
        return igccol
    finally:
        sys.path.pop()


def create_dem(config):
    """Create the SRTM DEM based on the configuration. In production, we
    take the datum and srtm_dir passed in. But for testing if the special
    variable ECOSTRESS_USE_AFIDS_ENV is defined then we use the value
    passed in from the environment."""
    datum = os.path.abspath(config["StaticAncillaryFileGroup", "Datum"])
    srtm_dir = os.path.abspath(config["StaticAncillaryFileGroup", "SRTMDir"])
    if "ECOSTRESS_USE_AFIDS_ENV" in os.environ:
        datum = os.environ["AFIDS_VDEV_DATA"] + "/EGM96_20_x100.HLF"
        srtm_dir = os.environ["ELEV_ROOT"]
    dem = geocal.SrtmDem(srtm_dir, False, geocal.DatumGeoid96(datum))
    return dem


def ortho_base_directory(config):
    """Create the ortho base. In production, take the directory passed in
    from the configuration file. But for testing, if ECOSTRESS_USE_AFIDS_ENV
    is defined then look for the location of this on pistol"""
    ortho_base_dir = os.path.abspath(config["StaticAncillaryFileGroup", "OrthoBase"])
    if "ECOSTRESS_USE_AFIDS_ENV" in os.environ:
        # Location on pistol, use if found, otherwise use setting in
        # run config file
        if os.path.exists("/raid22/band5_VICAR"):
            ortho_base_dir = "/raid22"
        elif os.path.exists("/data/smyth/Landsat/band5_VICAR"):
            ortho_base_dir = "/data/smyth/Landsat"
    return ortho_base_dir


def band_to_landsat_band(lband):
    if lband == 1:
        return geocal.Landsat7Global.BAND1
    elif lband == 2:
        return geocal.Landsat7Global.BAND2
    elif lband == 3:
        return geocal.Landsat7Global.BAND3
    elif lband == 4:
        return geocal.Landsat7Global.BAND4
    elif lband == 5:
        return geocal.Landsat7Global.BAND5
    elif lband == 61:
        return geocal.Landsat7Global.BAND61
    elif lband == 62:
        return geocal.Landsat7Global.BAND62
    elif lband == 7:
        return geocal.Landsat7Global.BAND7
    elif lband == 8:
        return geocal.Landsat7Global.BAND8
    else:
        raise RuntimeError("Unrecognized band number")


def create_lwm(config):
    """Create the land water mask. In production, use the directory passed
    in by the configuration file. But for testing if the special environment
    variable ECOSTRESS_USE_AFIDS_ENV is defined then look for the data at
    the standard location on pistol."""
    srtm_lwm_dir = os.path.abspath(config["StaticAncillaryFileGroup", "SRTMLWMDir"])
    if "ECOSTRESS_USE_AFIDS_ENV" in os.environ:
        # Location on pistol, use if found, otherwise use setting in
        # run config file
        if os.path.exists("/raid25/SRTM_2014_update/srtm_v3_lwm"):
            srtm_lwm_dir = "/raid25/SRTM_2014_update/srtm_v3_lwm"
    lwm = geocal.SrtmLwmData(srtm_lwm_dir, False)
    return lwm


def setup_spice(config):
    """Set up SPICE. In production, we use the directory passed in by
    configuration file. However, for testing if the special environment
    variable ECOSTRESS_USE_AFIDS_ENV is defined then we use the value passed
    in from the environment."""
    spice_data = os.path.abspath(config["StaticAncillaryFileGroup", "SpiceDataDir"])
    if "ECOSTRESS_USE_AFIDS_ENV" not in os.environ:
        os.environ["SPICEDATA"] = spice_data


def create_orbit_raw(
    config, pos_off=None, extrapolation_pad=5, large_gap=10, fix_l0_time_tag=False
):
    """Create orbit from L1A_RAW_ATT file"""
    # Spice is needed to work with the orbit data.
    setup_spice(config)
    orbfname = os.path.abspath(config["TimeBasedFileGroup", "L1A_RAW_ATT"])
    # Create orbit.
    if pos_off is not None:
        if fix_l0_time_tag:
            orb = EcostressOrbitL0Fix(orbfname, pos_off, extrapolation_pad, large_gap)
        else:
            orb = EcostressOrbit(orbfname, pos_off, extrapolation_pad, large_gap)
    else:
        if fix_l0_time_tag:
            orb = EcostressOrbitL0Fix(orbfname, extrapolation_pad, large_gap)
        else:
            orb = EcostressOrbit(orbfname, extrapolation_pad, large_gap)
    return orb


def create_time_table(fname, mirror_rpm, frame_time, time_offset=0):
    """Create the time table using the data from the given input."""
    return EcostressTimeTable(fname, mirror_rpm, frame_time, time_offset)


def create_scan_mirror(
    fname,
    max_encoder_value,
    first_encoder_value_0,
    second_encoder_value_0,
    instrument_to_sc_euler,
    first_angle_per_encoder_value,
    second_angle_per_encoder_value,
):
    """Create the scan mirror"""
    ev = h5py.File(fname, "r")["/FPIEencoder/EncoderValue"][:]
    sm = EcostressScanMirror(
        ev,
        max_encoder_value,
        first_encoder_value_0,
        second_encoder_value_0,
        instrument_to_sc_euler[0],
        instrument_to_sc_euler[1],
        instrument_to_sc_euler[2],
        first_angle_per_encoder_value,
        second_angle_per_encoder_value,
    )
    return sm


def is_day(igc):
    """Determine if the center pixel of the igc is in day or night, defined
    by having the solar elevation > 0"""
    ic = geocal.ImageCoordinate(igc.number_line / 2, igc.number_sample / 2)
    slv = geocal.CartesianFixedLookVector.solar_look_vector(igc.pixel_time(ic))
    gpt = igc.ground_coordinate(ic)
    sol_elv = 90 - geocal.LnLookVector(slv, gpt).view_zenith
    return sol_elv > 0


def aster_radiance_scale_factor():
    """Return the ASTER scale factors. This is for L1T data, found at
    https://lpdaac.usgs.gov/dataset_discovery/aster/aster_products_table/ast_l1t
    Our mosiac actually had adjustments made to make a clean mosaic, but this
    should be a reasonable approximation for going from the pixel integer data
    to radiance data in W/m^2/sr/um."""
    return [
        1.688,
        1.415,
        0.862,
        0.2174,
        0.0696,
        0.0625,
        0.0597,
        0.0417,
        0.0318,
        6.882e-3,
        6.780e-3,
        6.590e-3,
        5.693e-3,
        5.225e-3,
    ]


def ecostress_to_aster_band():
    """This is the mapping from the ASTER bands to the ECOSTRESS bands. Note that
    these aren't exact, these are just the closest match. There is no match
    for the 12.05 micron ecostress band, we reuse the 10.95 - 11.65 band. These
    band numbers are 1 based (matching the ASTER documentation)."""
    return [4, 10, 11, 12, 14, 14]


def ecostress_radiance_scale_factor(band):
    """Not sure what we will use here, right now we use the ASTER scale. Probably
    be something like this, since the dynamic range is somewhat similar. But in
    any case, for testing this is what we use.

    band is 0 based.
    """
    return aster_radiance_scale_factor()[ecostress_to_aster_band()[band] - 1]


def time_to_file_string(acquisition_time):
    """Return the portion of the ecostress filename based on the data acquisition
    date and time"""
    y, m, d, h, min, sec, *rest = re.split(r"[-T:.]", str(acquisition_time))
    return y + m + d + "T" + h + min + sec


def time_split(t):
    """Split a time into date and time, which we need to do for some of the
    metadata fields. Returns date, time"""
    mt = re.match(r"(.*)T(.*)Z", str(t))
    return mt.group(1), mt.group(2)


def ecostress_file_name(
    product_type,
    orbit,
    scene,
    acquisition_time,
    end_time=None,
    collection_label="ECOSTRESS",
    build="0100",
    version="01",
    extension=".h5",
    intermediate=False,
):
    """Create an ecostress file name from the given components."""
    if intermediate:
        front = ""
    else:
        front = collection_label + "_"
    if product_type == "L0B":
        return "%s%s_%05d_%s_%s_%s%s" % (
            front,
            product_type,
            orbit,
            time_to_file_string(acquisition_time),
            build,
            version,
            extension,
        )
    elif product_type == "Scene":
        return "%s%s_%05d_%s_%s%s" % (
            front,
            product_type,
            orbit,
            time_to_file_string(acquisition_time),
            time_to_file_string(end_time),
            extension,
        )
    elif scene is None:
        # Special handling for the couple of orbit based files
        return "%s%s_%05d_%s_%s_%s%s" % (
            front,
            product_type,
            orbit,
            time_to_file_string(acquisition_time),
            build,
            version,
            extension,
        )
    else:
        return "%s%s_%05d_%03d_%s_%s_%s%s" % (
            front,
            product_type,
            orbit,
            scene,
            time_to_file_string(acquisition_time),
            build,
            version,
            extension,
        )


def process_run(exec_cmd, out_fh=None, quiet=False):
    """This is like subprocess.run, but allowing a unix like 'tee' where
    we write the output to a log file and/or stdout.

    The command (which should be a standard array) is run, and the output
    is always returned. In addition, the output is written to the given
    out_fh is supplied, and to stdout if "quiet" is not True.
    """
    process = subprocess.Popen(
        exec_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    stdout = b""
    while True:
        output = process.stdout.readline()
        if output == b"" and process.poll() is not None:
            break
        if output:
            stdout = stdout + output
            if not quiet:
                print(output.strip().decode("utf-8"))
                sys.stdout.flush()
            if out_fh:
                print(output.strip().decode("utf-8"), file=out_fh)
                out_fh.flush()
    if process.poll() != 0:
        raise subprocess.CalledProcessError(process.poll(), exec_cmd, output=stdout)
    return stdout


def as_string(t):
    """Handle a variable that is either a bytes or a string, returning
    a string.

    This is to handle a change in h5py at about version 3 or so (see
    https://docs.h5py.org/en/latest/whatsnew/3.0.html). Things that
    use to return as str will now return as bytes.  Fortunately assignment
    takes either a bytes or a str without complaint, so this difference only
    matters if we doing something with a string.

    Note that h5py > 3.0 has a new asstr() type which returns a string
    (basically it like adding a ".decode('utf-8')". But for now we don't want to
    depend on h5py > 3.0, we want to support both h5py 2 and 3."""
    if hasattr(t, "decode"):
        return t.decode("utf-8")
    return t


def orbit_from_metadata(fname):
    """Read the standard metadata from the given file to return the orbit,
    scene, and acquisition_time for the given file."""
    fin = h5py.File(fname, "r")
    onum = fin["/StandardMetadata/StartOrbitNumber"][()]
    sid = fin["/StandardMetadata/SceneID"][()]
    bdate = as_string(fin["/StandardMetadata/RangeBeginningDate"][()])
    btime = as_string(fin["/StandardMetadata/RangeBeginningTime"][()])
    acquisition_time = geocal.Time.parse_time("%sT%sZ" % (bdate, btime))
    return int(onum), int(sid), acquisition_time


def determine_rotated_map_igc(igc, mi):
    """Rotate the given MapInfo so that it follows the path of the igc
    (which should be something like the minimum gore). We don't get
    the full coverage right here, but if you then use this in something
    like Resampler the coverage can be determined. This creates a rotated
    coordinate system where the center pixel at the start and ending line of
    the igc have a constant x value and varying y value, with the first line
    have the larger y value (e.g, if the rotation was 0 and y was latitude, we
    would have the larger latitude for the first line)"""
    gc1 = igc.ground_coordinate(geocal.ImageCoordinate(0, igc.number_sample / 2))
    gc2 = igc.ground_coordinate(
        geocal.ImageCoordinate(igc.number_line - 1, igc.number_sample / 2)
    )
    return determine_rotated_map(gc1, gc2, mi)


def determine_rotated_map(gc1, gc2, mi):
    """Rotate the given MapInfo so that it follows the path of the igc
    (which should be something like the minimum gore). We don't get
    the full coverage right here, but if you then use this in something
    like Resampler the coverage can be determined. This creates a rotated
    coordinate system where the center pixel at the start and ending line of
    the igc have a constant x value and varying y value, with the first line
    have the larger y value (e.g, if the rotation was 0 and y was latitude, we
    would have the larger latitude for the first line)"""
    x1, y1 = mi.coordinate(gc1)
    x2, y2 = mi.coordinate(gc2)
    a = math.atan2(x1 - x2, y1 - y2)
    rot = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    p = mi.transform
    pm = np.array([[p[1], p[2]], [p[4], p[5]]])
    pm2 = np.matmul(rot, pm)
    mi2 = geocal.MapInfo(
        mi.coordinate_converter,
        np.array([p[0], pm2[0, 0], pm2[0, 1], p[3], pm2[1, 0], pm2[1, 1]]),
        mi.number_x_pixel,
        mi.number_y_pixel,
        mi.is_point,
    )
    # In general, mi2 will cover invalid lat/lon. Just pull in to a reasonable
    # area, we handling the actual cover later
    mi2 = mi2.cover([geocal.Geodetic(10, 10), geocal.Geodetic(20, 20)])
    s = mi.resolution_meter / mi2.resolution_meter
    mi2 = mi2.scale(s, s)
    return mi2


__all__ = [
    "create_igc",
    "create_igccol",
    "create_dem",
    "ortho_base_directory",
    "band_to_landsat_band",
    "create_lwm",
    "setup_spice",
    "as_string",
    "create_orbit_raw",
    "create_time_table",
    "create_scan_mirror",
    "is_day",
    "aster_radiance_scale_factor",
    "ecostress_to_aster_band",
    "ecostress_radiance_scale_factor",
    "time_to_file_string",
    "time_split",
    "ecostress_file_name",
    "process_run",
    "find_radiance_file",
    "find_orbit_file",
    "orbit_from_metadata",
    "determine_rotated_map",
    "determine_rotated_map_igc",
    "create_igccol_from_qa",
]
