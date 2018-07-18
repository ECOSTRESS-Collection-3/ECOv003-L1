from .write_standard_metadata import *

class RadWriteStandardMetadata(WriteStandardMetadata):
    '''Add a few extra fields we use in l1b_rad'''
    def __init__(self, *args, line_order_flipped=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.line_order_flipped=line_order_flipped
            
    def write(self):
        super().write()
        pg = self.hdf_file[self.product_specfic_group]
        pg["RadScanLineOrder"] = "Reverse line order" if self.line_order_flipped else "Line order"
        
__all__ = ["RadWriteStandardMetadata"]
