from __future__ import annotations
from .l1b_geo_strategy import L1bGeoStrategy
from .l1b_tp_collect import L1bTpCollect
from datetime import timezone
import duckdb
import geocal
from loguru import logger
from multiprocessing.pool import Pool
from pathlib import Path
import os
import typing

if typing.TYPE_CHECKING:
    from .l1b_geo_process import L1bGeoProcess
    from ecostress_swig import EcostressIgcCollection


class L1bGeoStrategy3Pass(L1bGeoStrategy):
    """Do a three pass fit. We may well tweak this."""

    # This is empirical. We often have used 100, but gain a little
    # more coverage with just a little reduction in quality by going
    # to 75. Note that we don't want to go much lower. In collection
    # 2, we used 20 tiepoints and we had a fair number of scenes with
    # good matches but a lot with out. Seems better to dial it back.
    # Note we could have a difference between pass 1 and pass 2, but
    # at least for now use the same for both passes.
    min_tp_per_scene = 75

    # What we used in collection 2. This is in seconds, and is 3 scenes
    good_threshold = 3 * 52

    # Threshold to do a 2 point correction vs 1 point in pass 1. In seconds
    threshold_2_point = 6 * 52

    # Threshold for final accuracy estimate, if larger than this reject scene tiepoints.
    # In meters (not currently used, we can come back to this
    final_accuracy_estimate_threshold = 120

    def __init__(self, historical_orbit_data: str | os.PathLike[str]):
        self.historical_orbit_data = Path(historical_orbit_data)

    def collect_tp(
        self,
        l1b_geo_process: L1bGeoProcess,
        igccol: EcostressIgcCollection,
        pool: Pool | None,
        pass_number: int,
    ) -> geocal.TiePointCollection:
        """This is the standard image matching"""
        t = L1bTpCollect(
            igccol,
            l1b_geo_process.ortho_base,
            l1b_geo_process.lwm,
            l1b_geo_process.qa_file,
            fftsize=l1b_geo_process.l1b_geo_config.fftsize,
            magnify=l1b_geo_process.l1b_geo_config.magnify,
            magmin=l1b_geo_process.l1b_geo_config.magmin,
            toler=l1b_geo_process.l1b_geo_config.toler,
            redo=l1b_geo_process.l1b_geo_config.redo,
            ffthalf=l1b_geo_process.l1b_geo_config.ffthalf,
            seed=l1b_geo_process.l1b_geo_config.seed,
            num_x=l1b_geo_process.l1b_geo_config.num_x,
            num_y=l1b_geo_process.l1b_geo_config.num_y,
            proj_number_subpixel=l1b_geo_process.l1b_geo_config.proj_number_subpixel,
            min_tp_per_scene=self.min_tp_per_scene,
            min_number_good_scan=l1b_geo_process.l1b_geo_config.min_number_good_scan,
            pass_number=pass_number,
        )
        tpcol, _ = t.tpcol(pool=pool)
        return tpcol

    def collect_qa(
        self,
        l1b_geo_process: L1bGeoProcess,
        igccol: EcostressIgcCollection,
        tpcol: geocal.TiePointCollection,
        pass_number: int,
    ):
        # Like collection 2, except we really don't have info for assigning QA in
        # pass 1 or pass 2.
        tcorr_before = None
        tcorr_after = None
        geo_qa = None
        if pass_number == 3:
            tcorr_before = []
            tcorr_after = []
            geo_qa = []
            for i in range(igccol.number_image):
                num_tp = len([tp for tp in tpcol if tp.image_coordinate(i) is not None])
                igc = igccol.image_ground_connection(i)
                if hasattr(igc, "time_table"):
                    tt = igc.time_table
                else:
                    tt = igc.sub_time_table
                t = tt.min_time + (tt.max_time - tt.min_time)
                t1 = -9999.0
                t2 = -9999.0
                # Get points, but only if we actually have at
                # least on correction point
                if len(igc.orbit.parameter) > 0:
                    tb, ta = igccol.nearest_attitude_time_point(t)
                    if tb < geocal.Time.max_valid_time - 1:
                        t1 = t - tb
                    if ta < geocal.Time.max_valid_time - 1:
                        t2 = ta - t
                tcorr_before.append(t1)
                tcorr_after.append(t2)
                if t1 <= -9990 and t2 <= -9990:
                    geo_qa.append("Poor")
                else:
                    if t1 <= -9990:
                        min_delta = t2
                    elif t2 <= -9990:
                        min_delta = t1
                    else:
                        min_delta = min(t1, t2)
                    if num_tp >= self.min_tp_per_scene:
                        geo_qa.append("Best")
                    elif min_delta < self.good_threshold:
                        geo_qa.append("Good")
                    else:
                        geo_qa.append("Suspect")

                logger.info(
                    f"Scene {l1b_geo_process.scene_list[i]} geolocation accuracy QA: {geo_qa[-1]}"
                )
        l1b_geo_process.collect_qa(
            igccol,
            tpcol,
            pass_number=pass_number,
            tcorr_before=tcorr_before,
            tcorr_after=tcorr_after,
            geo_qa=geo_qa,
        )

    def filter_tp(
        self,
        tpcol: geocal.TiePointCollection,
        l1b_geo_process: L1bGeoProcess,
        igccol: EcostressIgcCollection,
        pool: Pool | None,
        pass_number: int,
    ) -> geocal.TiePointCollection:
        """No extra filtering for now. We have min_tp_per_scene in the tiepoint collection,
        but just take we get. We could play with throwing out outliers in pass 3 if
        too far off."""

        # Experimented with this, but we would actually need to move this out of this
        # step and do an iteration on the sba (toss out a scene, rerun). Final accuracy
        # only means something after we have run the SBA and fitted everything.
        #
        # Leave this here for reference, but we would need to rework this to actually
        # use
        #
        # The large bulk of the time scenes that pass our blunder detection etc
        # will pass the final_accuracy_estimate_threshold test. But we actually have
        # the occasional scene that can be way off. We probably want to just toss these out.
        # But we should investigate this a bit closer, it is possible this is pointing to
        # something real that we want to handle. We can go through our historical data and
        # find scenes with large final_accuracy error, and then look at the image data
        # to see what it going on. But this is future work
        if False:
            reject_list = []
            for i in range(igccol.number_image):
                if (
                    len([tp for tp in tpcol if tp.image_coordinate(i) is not None])
                    >= self.min_tp_per_scene
                ):
                    df = tpcol.data_frame(igccol, i)
                    final_accuracy_estimate = df.ground_2d_distance.quantile(0.68)
                    logger.info(
                        f"Final accuracy estimate scene {l1b_geo_process.scene_list[i]} {final_accuracy_estimate} m"
                    )
                    if final_accuracy_estimate > self.final_accuracy_estimate_threshold:
                        reject_list.append(i)
                        logger.info(
                            f"Final accuracy estimate scene {l1b_geo_process.scene_list[i]} {final_accuracy_estimate} m exceed the threshold, rejecting tiepoints for scene."
                        )

            for i in reject_list:
                tpcol = geocal.TiePointCollection(
                    [tp for tp in tpcol if tp.image_coordinate(i) is None]
                )

        return tpcol

    def modify_igc_pass_2(
        self,
        l1b_geo_process: L1bGeoProcess,
        igccol: EcostressIgcCollection,
        tpcol: geocal.TiePointCollection,
    ) -> None:
        """Add breakpoints. We currently add a breakpoint in the middle on any scene
        with tiepoints for pass 2. For pass 1, we use either 1 or 2 breakpoint. If we have
        a spread of data > threshold_2_point we put a breakpoint at the beginning and end of
        the orbit. Otherwise we put a single one in the middle."""
        orb = igccol.orbit
        tmin_all = None
        tmax_all = None
        for i in range(igccol.number_image):
            if (
                len([tp for tp in tpcol if tp.image_coordinate(i) is not None])
                >= self.min_tp_per_scene
            ):
                tmin, _, tmax = self.image_time(igccol, i)
                if tmin_all is None:
                    tmin_all = tmin
                    tmax_all = tmax
                tmax_all = max(tmax_all, tmax)
        if tmax_all is None:
            return
        if tmax_all - tmin_all > self.threshold_2_point:
            # Do the entire orbit. Not 100% sure we shouldn't use
            # tmin_all and tmax_all, but I think it makes sense to
            # extrapolate the corrections for scenes outside of where
            # we have tiepoints. It seems like the linear approximation
            # is a better guess if we have enough range in the tiepoints to
            # get a handle on the line.
            orb.insert_attitude_time_point(orb.min_time)
            orb.insert_attitude_time_point(orb.max_time)
        else:
            # Point in center of area we have tiepoints.
            orb.insert_attitude_time_point(tmin_all + (tmax_all - tmin_all) / 2)

    def modify_igc_pass_3(
        self,
        l1b_geo_process: L1bGeoProcess,
        igccol: EcostressIgcCollection,
        tpcol: geocal.TiePointCollection,
    ) -> None:
        """Add breakpoints. We currently add a breakpoint in the middle on any scene
        with tiepoints for pass 2. For pass 1, we use either 1 or 2 breakpoint. If we have
        a spread of data > threshold_2_point we put a breakpoint at the beginning and end of
        the orbit. Otherwise we put a single one in the middle."""
        orb = igccol.orbit
        for i in range(igccol.number_image):
            if (
                len([tp for tp in tpcol if tp.image_coordinate(i) is not None])
                >= self.min_tp_per_scene
            ):
                _, tmid, _ = self.image_time(igccol, i)
                orb.insert_attitude_time_point(tmid)

    def modify_igc(
        self,
        l1b_geo_process: L1bGeoProcess,
        igccol: EcostressIgcCollection,
        tpcol: geocal.TiePointCollection,
        pass_number: int,
    ) -> None:
        """Add breakpoints. We currently add a breakpoint in the middle on any scene
        with tiepoints for pass 2. For pass 1, we use either 1 or 2 breakpoint. If we have
        a spread of data > threshold_2_point we put a breakpoint at the beginning and end of
        the orbit. Otherwise we put a single one in the middle."""
        if pass_number == 2:
            return self.modify_igc_pass_2(l1b_geo_process, igccol, tpcol)
        elif pass_number == 3:
            return self.modify_igc_pass_3(l1b_geo_process, igccol, tpcol)
        raise RuntimeError("This shouldn't be able to happen")

    def add_historical_orbit_fit(
        self, l1b_geo_process: L1bGeoProcess, orbit: geocal.OrbitOffsetCorrection
    ) -> None:
        orbnum = l1b_geo_process.orbit_number
        # Look in database for surrounding orbits. This may not be there (and won't
        # ever be there for forward process). But for reprocessing we have this
        # historical information.
        tbefore = duckdb.query(
            f"select tend, tend_parm_0, tend_parm_1, tend_parm_2 from '{self.historical_orbit_data}' where orbit={orbnum - 1}"
        ).fetchall()
        tafter = duckdb.query(
            f"select tstart, tstart_parm_0, tstart_parm_1, tstart_parm_2 from '{self.historical_orbit_data}' where orbit={orbnum + 1}"
        ).fetchall()
        parm = []
        if len(tbefore) >= 1:
            att_tm, parm_0, parm_1, parm_2 = tbefore[0]
            tm = geocal.Time.parse_time(
                att_tm.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            )
            orbit.insert_attitude_time_point(tm)
            parm.extend([parm_0, parm_1, parm_2])
        if len(tafter) >= 1:
            att_tm, parm_0, parm_1, parm_2 = tafter[0]
            tm = geocal.Time.parse_time(
                att_tm.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            )
            orbit.insert_attitude_time_point(tm)
            parm.extend([parm_0, parm_1, parm_2])
        if len(parm) > 0:
            orbit.parameter = parm

    def correct_igc(
        self,
        l1b_geo_process: L1bGeoProcess,
        igccol_initial: EcostressIgcCollection,
        pool: Pool | None,
    ) -> tuple[EcostressIgcCollection, geocal.TiePointCollection]:
        """Do two passes through the data, a first global correction (either single
        attitude point or at beginning and end). Second pass that refines each scene"""
        igccol_initial.orbit = geocal.OrbitOffsetCorrection(igccol_initial.orbit)
        self.add_historical_orbit_fit(l1b_geo_process, igccol_initial.orbit)
        self.collect_qa(
            l1b_geo_process, igccol_initial, geocal.TiePointCollection(), pass_number=1
        )
        igccol_initial.orbit = geocal.OrbitOffsetCorrection(igccol_initial.orbit)
        igccol_corrected_pass2, tpcol_pass2 = self.correct_igc_pass(
            l1b_geo_process, igccol_initial, pool, pass_number=2
        )
        self.collect_qa(
            l1b_geo_process, igccol_corrected_pass2, tpcol_pass2, pass_number=2
        )
        # We add a error model on top of our existing one. I think that is what we want,
        # we hold the first pass orbit stable and just modify it
        igccol_corrected_pass2.orbit = geocal.OrbitOffsetCorrection(
            igccol_corrected_pass2.orbit
        )
        igccol_corrected, tpcol = self.correct_igc_pass(
            l1b_geo_process, igccol_corrected_pass2, pool, pass_number=3
        )
        self.collect_qa(l1b_geo_process, igccol_corrected, tpcol, pass_number=3)
        return (igccol_corrected, tpcol)


__all__ = [
    "L1bGeoStrategy3Pass",
]
