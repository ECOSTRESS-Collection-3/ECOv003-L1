from __future__ import annotations
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

    @abc.abstractmethod
    def modify_orbit(self, orb: geocal.Orbit) -> geocal.Orbit:
        """Create whatever changes are needed to have an orbit we can update."""
        raise NotImplementedError()

    def modify_igc(
        self,
        igccol: EcostressIgcCollection,
        tpcol: geocal.TiePointCollection,
        time_range_tp: list[tuple[int, geocal.Time, geocal.Time]],
        pass_number: int,
    ) -> None:
        """Whatever logic for adding breakpoints or whatever to the
        the igccol based on the tiepoints we got.
        We may well tweak this, but right now we set breakpoints at the
        beginning, middle and end of the scene, unless the beginning
        is within one scene of another breakpoint."""
        pass

    def correct_igc_pass(
        self,
        l1b_geo_process: L1bGeoProcess,
        igccol: EcostressIgcCollection,
        pool: Pool | None,
        pass_number: int,
    ) -> tuple[EcostressIgcCollection, geocal.TiePointCollection | None]:
        """Collect tie points, and used to correct the igccol"""
        logger.info(f"Starting pass {pass_number}")
        tpcol, time_range_tp = l1b_geo_process.collect_tp(igccol, pool, pass_number)
        if len(tpcol) == 0:
            logger.info("No tie-points, so skipping SBA correction")
            tpcol = None
            return igccol, None
        self.modify_igc(igccol, tpcol, time_range_tp, pass_number)
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
        should call collect_qa and the right points."""
        raise NotImplementedError()


class L1bCollection2GeoStrategy(L1bGeoStrategy):
    """The strategy we used for Collection 2. This was a single pass, and we
    added breakpoints for the scenes with tiepoints at beginning, middle,
    and end of the scenes"""

    def modify_orbit(self, orb: geocal.Orbit) -> geocal.Orbit:
        """Create whatever changes are needed to have an orbit we can update."""
        return geocal.OrbitOffsetCorrection(orb)

    def modify_igc(
        self,
        igccol: EcostressIgcCollection,
        tpcol: geocal.TiePointCollection,
        time_range_tp: list[tuple[int, geocal.Time, geocal.Time]],
        pass_number: int,
    ) -> None:
        """Add breakpoints for the scenes that we got good tiepoints from.
        We may well tweak this, but right now we set breakpoints at the
        beginning, middle and end of the scene, unless the beginning
        is within one scene of another breakpoint."""
        orb = igccol.orbit
        tlast = None
        for i, tmin, tmax in time_range_tp:
            if tlast is None and pass_number == 1:
                orb.insert_position_time_point(tmin)
            if tlast is None or tmin - tlast > 52.0:
                orb.insert_attitude_time_point(tmin)
            orb.insert_attitude_time_point(tmin + (tmax - tmin) / 2)
            orb.insert_attitude_time_point(tmax)
            tlast = tmax
        if tlast is not None and pass_number == 1:
            orb.insert_position_time_point(tlast)

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
        should call collect_qa and the right points."""
        igccol_corrected, tpcol = self.correct_igc_pass(
            l1b_geo_process, igccol_initial, pool, pass_number=1
        )
        l1b_geo_process.collect_qa(igccol_corrected, tpcol, pass_number=1)
        return (igccol_corrected, tpcol)
