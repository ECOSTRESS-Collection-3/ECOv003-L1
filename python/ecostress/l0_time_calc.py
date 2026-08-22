from __future__ import annotations
import numpy as np


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

    def __init__(self, hr_time: np.ndarray, time_error_correction: np.ndarray) -> None:
        """This take the L0B /hk/bad/hr/time time (the PS BAD time stamp, in GPS time)
        and the L0B /hk/bad/hr/time_error_correction (error correction, in seconds).
        We take the data for the full orbit
        """
        self._bad_time = hr_time
        self._bad_time_error_correction = time_error_correction

    def gps_time(
        self,
        time_fsw: np.ndarray,
        time_sync_fsw: np.ndarray,
        time_sync_fpie: np.ndarray,
    ) -> np.ndarray:
        """This take time_fsw, time_sync_fsw and time_sync_fpie for
        scene as returns j2000 times. This combines the data, and
        applies our corrections (see description of class for
        details).
        """
        # Correct fractional part of time_fsw, see description of class for details
        tfrac, tint = np.modf(time_fsw)
        time_fsw_fixed = tint + 1e3 * tfrac

        # Take median of time error corrections near the edges of the
        # scene. We add a buffer of 2 seconds just so we don't
        # truncate at the edges

        # TODO Add handling for bad time_fsw_fixed and bad bad_time_error_correction
        bcorr = np.median(
            self._bad_time_error_correction[
                (self._bad_time >= time_fsw_fixed.min() - 2)
                & (self._bad_time <= time_fsw_fixed.max() + 2)
            ]
        )

        # Note the sign on bcorr really is right here, this is just the convention used
        # by the ISS in reporting bad_time_error_correction. The 1e6 is because the
        # sync times are actually 1MHz counter values
        return time_fsw_fixed - bcorr + (time_sync_fpie - time_sync_fsw) * 1e-6


__all__ = [
    "L0TimeCalc",
]
