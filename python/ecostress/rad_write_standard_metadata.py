from __future__ import annotations
from .write_standard_metadata import WriteStandardMetadata
import numpy as np
from typing import Any


class RadWriteStandardMetadata(WriteStandardMetadata):
    """Add a few extra fields we use in l1b_rad"""

    def __init__(
        self,
        *args: Any,
        line_order_flipped: bool = False,
        cal_correction: None | np.ndarray = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.line_order_flipped = line_order_flipped
        self.cal_correction = cal_correction

    def write(self) -> None:
        super().write()
        pg = self.hdf_file[self.product_specfic_group]
        pg["RadScanLineOrder"] = (
            "Reverse line order" if self.line_order_flipped else "Line order"
        )
        if self.cal_correction is not None:
            pg.create_dataset(
                "CalibrationGainCorrection",
                data=self.cal_correction[0, :],
                dtype=np.float32,
            )
            pg.create_dataset(
                "CalibrationOffsetCorrection",
                data=self.cal_correction[1, :],
                dtype=np.float32,
            )
            pg["CalibrationGainCorrection"].attrs["Units"] = "dimensionless"
            pg["CalibrationOffsetCorrection"].attrs["Units"] = "W/m^2/sr/um"


__all__ = ["RadWriteStandardMetadata"]
