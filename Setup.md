Setup
=====

The software depends on AFIDS and the latest GeoCal. GeoCal is a subset of
AFIDS, but in separate repository which tends to run ahead of the version
we have GeoCal. GeoCal is also referred to as afids-python.

AFIDS Setup
-----------

The setup of AFIDS is as follows:

We install in a directory with the date (so we can have multiple versions).

    ../../Afids/configure --prefix=/pkg/afids/afids_20151103 \
        --with-blitz=build --with-gsl=build --with-hdf5=build \
	--with-hdf4=build --with-gnuplot=build --with-fftw=build \
	--with-geotiff=build --with-gdal=build --with-geos=build \
	--with-ogdi=build --with-openjpeg=build --with-afids-xvd=build \
	--with-afids-test-data=/home/smyth/AfidsData \
	--with-srtm-l2=/project/ancillary/SRTM/srtm_v3_dem_L2 \
	--without-afids-python
    make -j 12 all && make install && make autotools_install
    make -j 12 blas lapack umfpack swig
    scp pistol:/usr/share/aclocal/pkg.m4 /pkg/afids/afids_latest/share/aclocal

The blas etc. make line is stuff needed by the virtualenv described next,
but not needed by AFIDS when we build without afids_python.

We depend on pkg.m4 which isn't installed since we aren't building pkg,
so we just manually copy that from pistol. Nothing special about the pistol
version except it matches the autotools version we use in the Cartlab (which
is slightly older than the default one on the eco-scf system).

Python Setup
------------

GeoCal depends on a number of python packages. We set up a virtual environment
for this.

Make sure pip is the system pip, so "which pip" returns /usr/bin/pip
(so you aren't already in a virtualenv). Then if you haven't already
installed virtualenv do:

    pip install --user virtualenv

(can skip if you already have this).

Then

    cd /pkg/afids
    ~/.local/bin/virtualenv -p /usr/bin/python afids_pythonenv
    source afids_pythonenv/bin/activate

Need to link in the umfpack headers, or at least I couldn't figure out
a way to pass this to UMFPACK without linking here:

    mkdir -p afids_pythonenv/include
    ln -s /pkg/afids/afids_latest/include/umf* afids_pythonenv/include

Now install requirements. The various environment variables here are used
by different packages to know where to find things installed in
afids_latest rather than the system area:

    HDF5_DIR=/pkg/afids/afids_latest \
    BLAS=/pkg/afids/afids_latest/lib/libfblas.a \
    LAPACK=/pkg/afids/afids_latest/lib/libflapack.a \
    UMFPACK=/pkg/afids/afids_latest/lib/libumfpack.a \
    CFLAGS="-I/pkg/afids/afids_latest/include" \
    pip install -r ~/GeoCal/requirements.txt

GeoCal Setup
------------

TBD





