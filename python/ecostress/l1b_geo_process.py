from __future__ import annotations
from loguru import logger
import typing

if typing.TYPE_CHECKING:
    import types


class L1bGeoProcess:    
    '''Top level process for l1b_geo_process.

    Note that this is really just procedural process - do this, then do that sort of code.
    We use to have this just as a long script in l1b_geo_process, but it got to the point
    that breaking this up and having this in the python library made sense.'''
    def __init__(self,
                 run_config: Path | None = None,
                 l1a_raw_att: Path | None = None,
                 l1_osp_dir: Path | None = None,
                 l1b_rad: list[Path] | None = None,
                 ecostress_band: int = -1,
                 landsat_band: int = -1,
                 number_cpu: int = 10,
                 number_line: int = -1,
                 orbit_offset: list[float] | None = None):
        pass

    def run(self) -> None:
        '''Run the L1bGeoProcess'''
        pass
