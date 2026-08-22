import numpy as np

from ecostress.l0_time_calc import L0TimeCalc


def _make_scene_time_fsw(real_times):
    """Encode real_times the way L0A/L0B does: fractional part stored as if
    it were nanoseconds instead of microseconds (see L0TimeCalc docstring).
    """
    tint = np.floor(real_times)
    tfrac_real = real_times - tint
    return tint + tfrac_real / 1000.0


def test_gps_time_for_scene_normal():
    """No corruption: bcorr should just be the (constant) correction."""
    bad_time = np.arange(1000.0, 1200.0, 1.0)
    bad_tec = np.full_like(bad_time, 0.05)
    calc = L0TimeCalc(bad_time, bad_tec)

    real_times = np.linspace(1050.0, 1102.0, 44)
    time_fsw = _make_scene_time_fsw(real_times)
    sync_fsw = np.zeros(44)
    sync_fpie = np.zeros(44)

    out = calc.gps_time_for_scene(time_fsw, sync_fsw, sync_fpie)
    np.testing.assert_allclose(out, real_times - 0.05, atol=1e-6)


def test_gps_time_for_scene_corrupt_bad_time_error_correction_burst():
    """A minority-corrupted burst of bad_time_error_correction within the
    scene window should be excluded, and the median should be unaffected.
    """
    bad_time = np.arange(1000.0, 1200.0, 1.0)
    bad_tec = np.full_like(bad_time, 0.05)
    bad_tec[60:75] = 7.5e8  # bit-flip-like corruption burst
    calc = L0TimeCalc(bad_time, bad_tec)

    real_times = np.linspace(1050.0, 1102.0, 44)
    time_fsw = _make_scene_time_fsw(real_times)
    sync_fsw = np.zeros(44)
    sync_fpie = np.zeros(44)

    out = calc.gps_time_for_scene(time_fsw, sync_fsw, sync_fpie)
    np.testing.assert_allclose(out, real_times - 0.05, atol=1e-6)


def test_gps_time_for_scene_corrupt_time_fsw():
    """A single corrupt time_fsw sample shouldn't distort the scene time
    window used to select bad_time_error_correction, and the rest of the
    scene should still be correct.
    """
    bad_time = np.arange(1000.0, 1200.0, 1.0)
    bad_tec = np.full_like(bad_time, 0.05)
    calc = L0TimeCalc(bad_time, bad_tec)

    real_times = np.linspace(1050.0, 1102.0, 44)
    time_fsw = _make_scene_time_fsw(real_times)
    bad_idx = 10
    time_fsw[bad_idx] = (
        99999.0 + (real_times[bad_idx] - np.floor(real_times[bad_idx])) / 1000.0
    )

    out = calc.gps_time_for_scene(time_fsw, np.zeros(44), np.zeros(44))
    good = np.arange(44) != bad_idx
    np.testing.assert_allclose(out[good], real_times[good] - 0.05, atol=1e-6)


def test_gps_time_for_scene_falls_back_when_window_fully_corrupted():
    """If every bad_time_error_correction sample within the scene window is
    corrupt, fall back to the closest valid sample in the orbit rather than
    returning a corrupted median.
    """
    bad_time = np.arange(1000.0, 1200.0, 1.0)
    bad_tec = np.full_like(bad_time, 0.05)
    mask = (bad_time >= 1048) & (bad_time <= 1104)
    bad_tec[mask] = 6e8
    calc = L0TimeCalc(bad_time, bad_tec)

    real_times = np.linspace(1050.0, 1102.0, 44)
    time_fsw = _make_scene_time_fsw(real_times)

    out = calc.gps_time_for_scene(time_fsw, np.zeros(44), np.zeros(44))
    np.testing.assert_allclose(out, real_times - 0.05, atol=1e-6)
    # Valid data existed elsewhere in the orbit, so this is not the
    # no-uncorrupted-data-anywhere condition.
    assert calc.no_uncorrupted_bad_error_correction_data is False


def test_gps_time_for_scene_degrades_when_orbit_entirely_corrupted():
    """If there is no valid bad_time_error_correction data anywhere in the
    orbit, this is L1A - we would rather produce degraded output (using a
    correction of 0, i.e. leaving the BAD time stamp uncorrected) than fail
    outright, but we should flag that this happened so it can be checked
    downstream.
    """
    bad_time = np.arange(1000.0, 1200.0, 1.0)
    bad_tec = np.full_like(bad_time, 7e8)
    calc = L0TimeCalc(bad_time, bad_tec)
    assert calc.no_uncorrupted_bad_error_correction_data is False

    real_times = np.linspace(1050.0, 1102.0, 44)
    time_fsw = _make_scene_time_fsw(real_times)

    out = calc.gps_time_for_scene(time_fsw, np.zeros(44), np.zeros(44))
    # bcorr of 0 means time_fsw_fixed is returned uncorrected
    np.testing.assert_allclose(out, real_times, atol=1e-6)
    assert calc.no_uncorrupted_bad_error_correction_data is True
