from .write_standard_metadata import WriteStandardMetadata
import numpy as np


class RadWriteStandardMetadata(WriteStandardMetadata):
    """Add a few extra fields we use in l1b_rad"""

    def __init__(self, *args, line_order_flipped=False, cal_correction=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.line_order_flipped = line_order_flipped
        self.cal_correction = cal_correction

    def write(self):
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
