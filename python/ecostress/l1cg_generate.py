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
    generate a StructMetadata.0. This has information in a format called "ODL". We
    generated a sample of this using the HDFEOS library, but now we have a template
    that is easy for us to just directly use.

    Note that newer versions of GDAL can read the projection/map information from
    HDFEOS5 files.
    '''
    pass
    
