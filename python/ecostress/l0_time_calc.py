from __future__ import annotations
import numpy as np
from loguru import logger


class L0TimeCalc:
    """The ECOSTRESS instrument does not have its own absolute
    clock. Instead, it uses the ISS BAD time stamp collected from the
    1553 bus. It has a 100MHz counter, stepped to 1 MHz. It grabs the
    DPU-IO counter value when it takes the time stamp, and then the
    DPU-IO counter value when it collects the science data. These can
    be combined to give an absolute time for the science data.

    There are actually two time stamps on the ISS. The BAD time stamp,
    and a second time in the "Pointing and Support Data" (PS). The
    second time is what is reported with the ephemeris and attitude,
    and is the source of the time data in L1A_RAW_ATT files.

    There are several errors in the L0B timing.

    One error was fixed in version 7.13 of the L0B software, an error
    in interpreting the PS time stamp. This affected the timing in the
    L1A_RAW_ATT file. The time tag had two parts, a Time_coarse which
    gave the seconds a Time_fine for the fractional part. The time tag
    is suppose to be calculated as Time_coarse + Time_fine / 256.0,
    but L0B was instead calculating this as Time_coarse + 1.0 /
    Time_fine. This was fixed in L0B processing. We have a separate
    class EcostressOrbitL0Fix that can be used for older data,
    translating the incorrect time stamp pre 7.13 into the correct
    time stamp. Note that most of the time L1A_RAW_ATT with a version
    number >= 7.13. However as of August 2026 there was still some old
    versions of the L0B data used as input to L1A processing. You can
    check the input pointer in L1A_RAW_ATT to determine the version
    used. We have that automatically done in L1B_GEO starting with
    8.03 (see the git Issue #178). That is done external to this class.

    The second error was a known error in BAD time stamp.

    From “International Space Station (ISS) Guidance Navigation and
    Control System (GNC) Memo for Payloads – January 2015”:

       “The time functionality on ISS was intended to use an auto-sync
       feature such that the central computer on the ISS, the computer
       and control computer (C&C), would sync its clock to the time
       output from the GPS receiver in the SIGIs.  However, due to
       various reasons, the C&C computer clocks are allowed to drift
       with respect to the SIGI time by up to +/- 1 second.  The
       operators adjust a drift compensation parameter to adjust the
       C&C clock to keep the error to within 1 second.  All other ISS
       computers sync to the C&C computer, and each ISS computer
       provides a time stamp for all data messages and a broadcast
       time via SubAddress 29 (reference SSP 41175-02).  That time
       stamp will also be in error by +/- 1 second.  However, the GNC
       computer computes the time error of the C&C computer as
       compared to the SIGI GPS time and provides that time error in
       BAD data.  The time stamp of each data packet can be adjusted
       by adding the time error to create a time stamp that is
       accurate to within +/- 55 microseconds.”

    Note that is affects the BAD time stamp, but *not* the PS time
    stamp which does not have this issue. So we need to adjust the
    science data times, but not the ephemeris/atittude times.

    The BAD error correction is supplied in the same packets that give
    the ephemeris and attitude (so collected at the rate of about 1
    per second). It is somewhat confusing that the data comes with the
    ephemeris/attitude and yet it doesn't actually apply to them. In a
    perfect world, we would get this at the same rate as the science
    data time stamp, however that is not what we have.

    For most of the time, the BAD error correction is almost constant
    over a scene. A AI analysis of the full mission data found that
    99% of the data is within 2.5 microseconds over the 52 seconds of
    the scene, and the absolute maximum excluding corrupted data is 18
    microseconds.  This gives about 0.14 m error for a 70 m pixel, so
    this is essentially zero. However we do occasionally get a corrupt
    error correction time stamp.  So we just take the median value
    over the time of the scene, which is good enough.

    A follow-up AI analysis looking for corrupt bad_time_error_correction
    values mission wide found that genuine values are essentially always
    within +/-1 second, with rare (a handful of orbits out of the full
    mission) genuine step changes of a few seconds within a single scene
    (real ISS clock discipline events, not corruption). But there is a
    large, completely empty gap in the per-orbit maximum magnitude between
    about 25 seconds and about 395,000 seconds - no genuine value, and no
    known corrupted value, ever falls in that range. Two distinct known
    corruption modes land well above that gap: garbled/bit-flip-like
    telemetry (values of order 1e8-8e8 seconds) and an apparent GPS
    week-number rollover bug (values within a fraction of a second of
    +/-604800, i.e. exactly one week). So we treat any
    bad_time_error_correction sample with a magnitude at or above
    CORRUPT_TIME_ERROR_CORRECTION_THRESHOLD as corrupt and exclude it before
    taking the median. Note this threshold intentionally does *not* try to
    catch corruption in the plausible few-second range (that also occurs,
    but rarely, and can't be distinguished from a genuine fast clock
    correction step by magnitude alone); the wide scene-spanning median
    window already gives good robustness against that since it takes a
    large number of samples across the whole scene, not just a couple of
    points at the edges.

    We also saw the occasional corrupt time_fsw value (the L0A/L0B science
    data time stamp), which if used directly for time_fsw_fixed.min()/max()
    can badly distort the scene time window used to select
    bad_time_error_correction samples. We guard against this the same way,
    by excluding time_fsw values that are wildly inconsistent (more than
    CORRUPT_TIME_FSW_THRESHOLD seconds from the median) with the rest of the
    scene before taking min/max.

    Finally, we occasionally see the scene's time window contain no valid
    (non-corrupt) bad_time_error_correction samples at all - either because
    of a real gap in BAD telemetry (this happens fairly often right at the
    start of a scene) or because every sample nearby happens to be
    corrupted. In that case we fall back to the single closest valid sample
    anywhere in the orbit, logging a warning since that value may be stale.

    It is possible (though not seen so far) for an entire orbit to have no
    valid bad_time_error_correction data at all, so there is nothing to fall
    back to. This is L1A - we would rather produce degraded output than no
    output at all, since a downstream user/QA process can decide whether
    degraded data for a given scene/orbit is usable. So rather than raising
    an exception in this case, we log a warning, use a correction of 0
    (i.e., leave the BAD time stamp uncorrected - within a second or so, per
    the ISS spec quoted above, rather than an arbitrary/nonsensical value),
    and set the no_uncorrupted_bad_error_correction_data flag so callers can
    check after the fact whether this happened and decide how to handle it
    (e.g. flagging the affected scenes as degraded quality downstream).

    The third error is a L0A error. The BAD time stamp associated with
    the science data is made up of two pieces, a count of seconds and
    a fractional part. The L0A incorrectly handles the fractional part
    as a count of nanoseconds. It is actually microseconds. Ideally
    L0A would be changed to fix this (like we previously did for the
    L0B error). However, it would be very difficult to rerun L0A, the
    input data is not kept. This is also something easy to fix in L1A,
    so we have the fix here. L0A and L0B continue reporting the wrong
    time, but we can just pull off the fractional part in L1A multiple
    by 1000 to convert to the correct time scale, and put back. The L0
    software only uses the time for ordering packets, so even though
    it is using the wrong time it is getting the right order for
    everything. So we have elected to leave the L0 software alone and
    correct this here.

    This class handles all these pieces to come up with a correct time
    stamp.  We take in the entire L0B data for the BAD time
    correction, and then we take the three time pieces (time_fsw,
    time_sync_fpie, time_sync_fsw) and combine to give a final time.
    A couple of notes of things that might be confusing.  The BAD
    times are relative to the GPS epoch, we report the final time in
    gps timing also to match what L1A needs. L1A converts this to
    j2000 later, which is what the downstream processing needs. The
    time_sync_fsw and time_sync_fpie aren't actually times, despite
    the names. These are instead counter values of the 1MHz counter.

    Also, the 1MHz counter is frequently reset to 0. I'm not sure of
    the exact reason for this, but you can see this in the data. This
    can happen several times in a single orbit, although it seems more
    to be about once an orbit or so. This doesn't matter since it
    doesn't reset in a scene. We only need the relative difference
    between time_sync_fpie and time_sync_fsw so this doesn't
    matter. But if you try to compare DPU-IO counts across data
    (e.g. from one orbit to the next, or even one scene to the next)
    this is often meaningless because you don't know if the counter
    has be set back to 0 or not. This doesn't cause any problems, but
    be aware of this.

    """

    # See discussion above. Any bad_time_error_correction sample with a
    # magnitude at or above this (seconds) is treated as corrupt and
    # excluded. Chosen to sit in the middle of the empty gap (~25s to
    # ~395,000s) found in the mission-wide analysis, so it can't accidentally
    # reject genuine data.
    CORRUPT_TIME_ERROR_CORRECTION_THRESHOLD = 50.0

    # A scene is 52 seconds. Any time_fsw sample more than this many seconds
    # from the median time_fsw for the scene is treated as corrupt and
    # excluded before computing the scene's time_fsw_fixed.min()/max(). This
    # is intentionally more than half a scene so we don't reject legitimate
    # samples near the edges of the scene.
    CORRUPT_TIME_FSW_THRESHOLD = 60.0

    def __init__(self, hr_time: np.ndarray, time_error_correction: np.ndarray) -> None:
        """This take the L0B /hk/bad/hr/time time (the PS BAD time stamp, in GPS time)
        and the L0B /hk/bad/hr/time_error_correction (error correction, in seconds).
        We take the data for the full orbit
        """
        self._bad_time = hr_time
        self._bad_time_error_correction = time_error_correction

        # Flag that gets set to True if we ever hit the (expected to be
        # very rare) condition of having no uncorrupted
        # bad_time_error_correction data anywhere in the orbit to fall back
        # on, for any scene processed by this instance. Starts False, and is
        # sticky (stays True) once set, since a single instance covers the
        # whole orbit and downstream code may process many scenes with it -
        # this lets a caller check once at the end whether *any* scene in
        # the orbit hit this degraded-quality condition, rather than having
        # to check the return value of every single gps_time_for_scene() call.
        self.no_uncorrupted_bad_error_correction_data = False

    def gps_time_for_scene(
        self,
        time_fsw: np.ndarray,
        time_sync_fsw: np.ndarray,
        time_sync_fpie: np.ndarray,
    ) -> np.ndarray:
        """This take time_fsw, time_sync_fsw and time_sync_fpie for
        scene as returns j2000 times. This combines the data, and
        applies our corrections (see description of class for
        details).

        Note the data passed in should be for a single scene, not a full
        orbit or multiple scenes. The corrupt-data handling here (see
        _robust_time_fsw_range and _robust_bad_time_error_correction) relies
        on knowing a scene is 52 seconds long - it uses that to decide
        whether a given time_fsw or bad_time_error_correction sample is
        wildly inconsistent with the rest and should be treated as corrupt.
        If you pass in more than a scene of data (e.g. a whole orbit), that
        assumption no longer holds and the corrupt-data checks will not
        behave correctly (they may reject genuine samples, or fail to
        reject actually corrupt ones).
        """
        # Correct fractional part of time_fsw, see description of class for details
        tfrac, tint = np.modf(time_fsw)
        time_fsw_fixed = tint + 1e3 * tfrac

        tmin, tmax = self._robust_time_fsw_range(time_fsw_fixed)
        bcorr = self._robust_bad_time_error_correction(tmin, tmax)

        # Note the sign on bcorr really is right here, this is just the convention used
        # by the ISS in reporting bad_time_error_correction. The 1e6 is because the
        # sync times are actually 1MHz counter values
        return time_fsw_fixed - bcorr + (time_sync_fpie - time_sync_fsw) * 1e-6

    def _robust_time_fsw_range(self, time_fsw_fixed: np.ndarray) -> tuple[float, float]:
        """Return (min, max) of time_fsw_fixed for the scene, excluding any
        samples that are wildly inconsistent with the rest (a corrupt
        time_fsw_fixed value), since a single corrupt value would otherwise
        badly distort the min/max and hence the scene time window used to
        select bad_time_error_correction samples.
        """
        med = np.median(time_fsw_fixed)
        good = np.abs(time_fsw_fixed - med) <= self.CORRUPT_TIME_FSW_THRESHOLD
        n_bad = int((~good).sum())
        if n_bad == 0:
            return float(time_fsw_fixed.min()), float(time_fsw_fixed.max())
        if not np.any(good):
            logger.warning(
                "All time_fsw values for this scene disagree with each other "
                f"by more than {self.CORRUPT_TIME_FSW_THRESHOLD}s. Falling "
                "back to the raw min/max; results may be unreliable."
            )
            return float(time_fsw_fixed.min()), float(time_fsw_fixed.max())
        logger.warning(
            f"Found {n_bad} corrupt time_fsw value(s) for this scene (more "
            f"than {self.CORRUPT_TIME_FSW_THRESHOLD}s from the scene "
            "median). Excluding these before determining the scene time window."
        )
        good_vals = time_fsw_fixed[good]
        return float(good_vals.min()), float(good_vals.max())

    def _robust_bad_time_error_correction(self, tmin: float, tmax: float) -> float:
        """Return the median bad_time_error_correction over the scene
        [tmin, tmax], robust to corrupt sample values (see class
        description). We add a buffer of 2 seconds just so we don't truncate
        at the edges.
        """
        in_scene = (self._bad_time >= tmin - 2) & (self._bad_time <= tmax + 2)
        candidate = self._bad_time_error_correction[in_scene]

        good = np.abs(candidate) < self.CORRUPT_TIME_ERROR_CORRECTION_THRESHOLD
        n_bad = int((~good).sum())
        if n_bad > 0:
            logger.warning(
                f"Found {n_bad} corrupt bad_time_error_correction value(s) "
                f"(|value| >= {self.CORRUPT_TIME_ERROR_CORRECTION_THRESHOLD}s) "
                "near this scene. Excluding these before taking the median."
            )
        good_candidate = candidate[good]

        if len(good_candidate) > 0:
            return float(np.median(good_candidate))

        logger.warning(
            "No valid bad_time_error_correction samples found within the "
            "scene time window (either a gap in BAD telemetry, or everything "
            "nearby is corrupt). Falling back to the closest valid sample "
            "anywhere in the orbit."
        )
        return self._closest_valid_bad_time_error_correction(0.5 * (tmin + tmax))

    def _closest_valid_bad_time_error_correction(self, t: float) -> float:
        """Fall back for when the scene time window has no valid
        bad_time_error_correction samples: return the value of the single
        closest valid (non-corrupt) sample anywhere in the orbit.
        """
        good = (
            np.abs(self._bad_time_error_correction)
            < self.CORRUPT_TIME_ERROR_CORRECTION_THRESHOLD
        )
        if not np.any(good):
            # This is L1A, and we would rather produce degraded output than
            # fail outright - a downstream QA process can decide whether
            # this scene/orbit is usable. Use a correction of 0 (i.e., leave
            # the BAD time stamp uncorrected) since that is a bounded, sane
            # fallback (the ISS spec says the uncorrected error is within
            # +/-1 second - see class description) rather than propagating
            # a corrupted or arbitrary value. Set the sticky flag so this
            # can be detected and handled downstream.
            logger.warning(
                "No valid bad_time_error_correction samples found anywhere "
                "in this orbit - all data is corrupt. Using a correction of "
                "0 and setting no_uncorrupted_bad_error_correction_data."
            )
            self.no_uncorrupted_bad_error_correction_data = True
            return 0.0
        good_time = self._bad_time[good]
        good_value = self._bad_time_error_correction[good]
        idx = np.argmin(np.abs(good_time - t))
        distance = abs(good_time[idx] - t)
        if distance > 10:
            logger.warning(
                f"Closest valid bad_time_error_correction sample is "
                f"{distance:.1f}s away from the scene - value may be stale."
            )
        return float(good_value[idx])


__all__ = [
    "L0TimeCalc",
]
