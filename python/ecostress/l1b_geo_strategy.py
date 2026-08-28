from __future__ import annotations
from .l1b_tp_collect import L1bTpCollect
import abc
import geocal  # type: ignore
from ecostress_swig import (  # type: ignore
    EcostressIgcCollection,
)
from loguru import logger
from multiprocessing.pool import Pool
import typing

if typing.TYPE_CHECKING:
    from .l1b_geo_process import L1bGeoProcess


class L1bGeoStrategy(object, metaclass=abc.ABCMeta):
    """This handles the strategy we use to improve geolocation in L1bGeoProcess.
    Over time this class may well go away, but for now it is nice to have separate
    strategies that we can run and still have other ones around to compare.

    This works closely with L1bGeoProcess.
    """

    def collect_qa(
        self,
        l1b_geo_process: L1bGeoProcess,
        igccol: EcostressIgcCollection,
        tpcol: geocal.TiePointCollection,
        pass_number: int,
    ):
        good_threshold = 3 * 52
        tcorr_before = []
        tcorr_after = []
        geo_qa = []
        for i in range(igccol.number_image):
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
                if min_delta < 50 / 2:
                    geo_qa.append("Best")
                elif min_delta < good_threshold:
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

    def modify_igc(
        self,
        l1b_geo_process: L1bGeoProcess,
        igccol: EcostressIgcCollection,
        tpcol: geocal.TiePointCollection,
        pass_number: int,
    ) -> None:
        """Whatever logic for adding breakpoints or whatever to the
        the igccol based on the tiepoints we got."""
        pass

    def image_time(
        self, igccol: EcostressIgcCollection, image_index: int
    ) -> tuple[geocal.Time, geocal.Time, geocal.Time]:
        """Return the image start, mid, and end time."""
        tt = igccol.image_ground_connection(image_index).time_table
        return tt.min_time, tt.min_time + (tt.max_time - tt.min_time) / 2, tt.max_time

    def collect_tp(
        self,
        l1b_geo_process: L1bGeoProcess,
        igccol: EcostressIgcCollection,
        pool: Pool | None,
        pass_number: int,
    ) -> geocal.TiePointCollection:
        return (geocal.TiePointCollection, [])

    def filter_tp(
        self,
        tpcol: geocal.TiePointCollection,
        l1b_geo_process: L1bGeoProcess,
        igccol: EcostressIgcCollection,
        pool: Pool | None,
        pass_number: int,
    ) -> geocal.TiePointCollection:
        """Filter the tiepoints however the strategy does."""
        return tpcol

    def correct_igc_pass(
        self,
        l1b_geo_process: L1bGeoProcess,
        igccol: EcostressIgcCollection,
        pool: Pool | None,
        pass_number: int,
    ) -> tuple[EcostressIgcCollection, geocal.TiePointCollection | None]:
        """Collect tie points, and used to correct the igccol"""
        logger.info(f"Starting pass {pass_number}")
        tpcol = self.collect_tp(l1b_geo_process, igccol, pool, pass_number)
        tpcol = self.filter_tp(tpcol, l1b_geo_process, igccol, pool, pass_number)
        if len(tpcol) == 0:
            logger.info("No tie-points, so skipping SBA correction")
            tpcol = geocal.TiePointCollection()
            igccol_corrected = igccol
        else:
            self.modify_igc(l1b_geo_process, igccol, tpcol, pass_number)
            igccol_corrected = l1b_geo_process.run_sba(igccol, tpcol, pass_number)
        logger.info(f"Done with pass {pass_number}")
        return igccol_corrected, tpcol

    @abc.abstractmethod
    def correct_igc(
        self,
        l1b_geo_process: L1bGeoProcess,
        igccol_initial: EcostressIgcCollection,
        pool: Pool | None,
    ) -> tuple[EcostressIgcCollection, geocal.TiePointCollection]:
        """Do whatever we are going to do to generate the final corrected
        EcostressIgcCollection, and the final tiepoints used. This might
        have multiple passes, depending on the strategy. Note that this
        can use l1b_geo_process for various calculations, and in particular
        should call collect_qa at the right points."""
        raise NotImplementedError()


class L1bCollection2GeoStrategy(L1bGeoStrategy):
    """The strategy we used for Collection 2. This was a single pass, and we
    added breakpoints for the scenes with tiepoints at beginning, middle,
    and end of the scenes"""

    def modify_igc(
        self,
        l1b_geo_process: L1bGeoProcess,
        igccol: EcostressIgcCollection,
        tpcol: geocal.TiePointCollection,
        pass_number: int,
    ) -> None:
        """Add breakpoints for the scenes that we got good tiepoints from.
        We may well tweak this, but right now we set breakpoints at the
        beginning, middle and end of the scene, unless the beginning
        is within one scene of another breakpoint."""
        orb = igccol.orbit
        tlast = None
        # Note collection 2 used time_range_tp, which had problems in that it
        # has extra points in it. Duplicate this for backwards compatibility, but
        # this should really have used image_time instead to get this information.
        for i, tmin, tmax in self._time_range_tp:
            if tlast is None and pass_number == 1:
                orb.insert_position_time_point(tmin)
            if tlast is None or tmin - tlast > 52.0:
                orb.insert_attitude_time_point(tmin)
            orb.insert_attitude_time_point(tmin + (tmax - tmin) / 2)
            orb.insert_attitude_time_point(tmax)
            tlast = tmax
        if tlast is not None and pass_number == 1:
            orb.insert_position_time_point(tlast)

    def collect_tp(
        self,
        l1b_geo_process: L1bGeoProcess,
        igccol: EcostressIgcCollection,
        pool: Pool | None,
        pass_number: int,
    ) -> geocal.TiePointCollection:
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
            min_tp_per_scene=l1b_geo_process.l1b_geo_config.min_tp_per_scene,
            min_number_good_scan=l1b_geo_process.l1b_geo_config.min_number_good_scan,
            pass_number=pass_number,
        )
        tpcol, self._time_range_tp = t.tpcol(pool=pool)
        return tpcol

    def correct_igc(
        self,
        l1b_geo_process: L1bGeoProcess,
        igccol_initial: EcostressIgcCollection,
        pool: Pool | None,
    ) -> tuple[EcostressIgcCollection, geocal.TiePointCollection]:
        igccol_initial.orbit = geocal.OrbitOffsetCorrection(igccol_initial.orbit)
        igccol_corrected, tpcol = self.correct_igc_pass(
            l1b_geo_process, igccol_initial, pool, pass_number=1
        )
        self.collect_qa(l1b_geo_process, igccol_corrected, tpcol, pass_number=1)
        return (igccol_corrected, tpcol)


__all__ = ["L1bGeoStrategy", "L1bCollection2GeoStrategy"]
