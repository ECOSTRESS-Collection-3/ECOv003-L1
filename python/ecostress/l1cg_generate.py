import geocal  # type: ignore
import os
import h5py

class L1cgGenerate:
    '''The L1CG product is HDFEOS5. This isn't something I would have necessarily
    picked, HDFEOS5 really was never used very widely. But this was put in for
    collection 2, and we want to support the format.

    We can mostly generate this using the standard h5py library. While there is
    a HDFEOS5 library (with limited support in our swig/C++ code) it is actually
    easier just to use h5py. HDFEOS is a HDF5 file with some conventions, see
    the document https://www.earthdata.nasa.gov/s3fs-public/imported/ESDS-RFC-008-v1.1.pdf
    for a description of this. Primarily we need a specific (simple) convention about
    where to put grids, fields in those grid, and various metadata. Also, we
    generate a StructMetadata.0. This has information in a format called "ODL".
    We use the C++/SWIG to generate a initial HDFEOS file, and then just reopen this
    with h5py to populate this.

    Note that newer versions of GDAL can read the projection/map information from
    HDFEOS5 files.
    '''
    def __init__(self, l1b_geo, l1b_rad, output_name, local_granule_id=None,
                 resolution=70, number_subpixel=3):
        self.l1b_geo = l1b_geo
        self.l1b_rad = l1b_rad
        self.output_name = output_name
        if local_granule_id:
            self.local_granule_id = local_granule_id
        else:
            self.local_granule_id = os.path.basename(output_name)
        self.resolution = resolution
        self.number_subpixel = number_subpixel

    def run(self):
        # TODO Make sure to update bounding box stuff in output metadata
        fout = h5py.File(self.output_name, "w")
        #m = self.l1b_geo_generate.m.copy_new_file(
        #    fout, self.local_granule_id, "ECO_L1CG_RAD"
        #)

    
__all__ = ["L1cgGenerate"]
