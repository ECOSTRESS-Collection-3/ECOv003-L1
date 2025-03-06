from ecostress.l1b_rad_simulate import L1bRadSimulate
from geocal import SpiceHelper
from multiprocessing import Pool
import os
import pytest
from pathlib import Path


@pytest.mark.long_test
def test_l1b_rad_simulate(
    isolated_dir, igc_old, old_test_data, aster_mosaic_surface_data
):
    l1b_sim = L1bRadSimulate(
        igc_old.ipi.orbit,
        igc_old.ipi.time_table,
        igc_old.ipi.camera,
        aster_mosaic_surface_data,
        raycast_resolution=100.0,
    )
    fout = Path("ECOSTRESS_L1B_RAD_80001_001_20150114_1024020211_0100_01.h5").absolute()
    # Limitation of test data is that it expects to be in end_to_end_testing
    # directory because of relative paths.
    curdir = os.getcwd()
    # Bug that we seem to need to do this to force spice to be loaded before
    # we create the pool. Would like to figure out why this happens and fix this
    SpiceHelper.spice_setup()
    try:
        os.chdir(old_test_data)
        pool = Pool(20)
        l1b_sim.create_file(
            fout,
            pool=pool,
        )
    finally:
        os.chdir(curdir)
