from __future__ import annotations
from .run_config import RunConfig
from pathlib import Path
from loguru import logger
from functools import cached_property
import sys
import types
import typing

if typing.TYPE_CHECKING:
    pass


class L1bGeoProcess:
    """Top level process for l1b_geo_process.

    Note that this is really just procedural process - do this, then do that sort of code.
    We use to have this just as a long script in l1b_geo_process, but it got to the point
    that breaking this up and having this in the python library made sense."""

    def __init__(
        self,
        prod_dir: Path,
        run_config: Path | None = None,
        l1a_raw_att: Path | None = None,
        l1_osp_dir: Path | None = None,
        l1b_rad: list[Path] | None = None,
        ecostress_band: int = -1,
        landsat_band: int = -1,
        number_cpu: int = 10,
        number_line: int = -1,
        orbit_offset: list[float] | None = None,
    ):
        self.prod_dir = prod_dir.absolute()
        if run_config is not None:
            self.process_run_config(run_config)
        else:
            if l1a_raw_att is None or l1_osp_dir is None or l1b_rad is None:
                raise RuntimeError(
                    "Need to supply either run_config or l1a_raw_att, l1_osp_dir and l1b_rad"
                )
            self.process_args(l1a_raw_att, l1_osp_dir, l1b_rad)

    @cached_property
    def l1b_geo_config(self) -> type.ModuleType:
        try:
            sys.path.append(self.l1_osp_dir)
            import l1b_geo_config
            return l1b_geo_config
        finally:
            sys.path.remove(self.l1_osp_dir)

    def process_run_config(self, run_config: Path) -> None:
        """Set up things using run config, if supplied"""
        config = RunConfig(run_config)
        self.l1_osp_dir = Path(config["StaticAncillaryFileGroup", "L1_OSP_DIR"]).absolute()
        self.ncpu = int(config["Process", "NumberCpu"])
        fix_l0_time_tag
        if hasattr(self.l1b_geo_config, "fix_l0_time_tag") and self.l1b_geo_config.fix_l0_time_tag:
            fix_l0_time_tag = True
        self.orb = create_orbit_raw(
            config,
            pos_off=self.l1b_geo_config.x_offset_iss,
            extrapolation_pad=self.l1b_geo_config.extrapolation_pad,
            large_gap=self.l1b_geo_config.large_gap,
            fix_l0_time_tag=fix_l0_time_tag,
        )

    def process_args(
        self,
        l1a_raw_att: Path,
        l1_osp_dir: Path,
        l1b_rad: list[Path],
    ) -> None:
        """Set up things using command line arguments, if supplied"""
        pass

    def run(self) -> None:
        """Run the L1bGeoProcess"""
        pass
