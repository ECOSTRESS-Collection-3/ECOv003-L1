Setup
=====

The software depends on AFIDS and the latest GeoCal. GeoCal is a subset of
AFIDS, but in separate repository which tends to run ahead of the version
we have GeoCal. GeoCal is also referred to as afids-python.

The dependencies are:

* [AFIDS Software](https://github.jpl.nasa.gov/Cartography/afids)
* [AFIDS Test Data](https://github.jpl.nasa.gov/Cartography/afids-data) - test data used by unit tests, only needed if you want to run the AFIDS unit tests (so not needed to just build the software).
* [GeoCal] (https://github.jpl.nasa.gov/Cartography/geocal) - this is part of AFIDS, however we also make this subset available on its own for use in areas where we don't want the full AFIDS package. This particular packages also contains more recent changes that haven't yet been merged in the the AFIDS Software package (it is under active development).

Get this software, for example:

    cd ~
    git clone git@github.jpl.nasa.gov:Cartography/afids.git Afids
    git clone git@github.jpl.nasa.gov:Cartography/afids-data.git AfidsData
    git clone git@github.jpl.nasa.gov:Cartography/geocal.git GeoCal

AFIDS Setup
-----------

The setup of AFIDS is as follows:

We install in a directory with the date (so we can have multiple versions).

Before building, make sure to remove the old afids_latest, so we don't think
we already have thirdparty stuff available.

    cd ~
    mkdir -p AfidsBuild/build_afids_install
    cd AfidsBuild/build_afids_install
    /home/smyth/Afids/configure --prefix=/pkg/afids/afids_20161207 \
       THIRDPARTY=build_needed --with-afids-python=no --with-python=build \
       --with-afids-test-data=/home/smyth/AfidsData \
       --with-srtm-l2=/project/ancillary/SRTM/srtm_v3_dem_L2 --with-tcl=build
    make -j 12 all && make install && make autotools_install
    make -j 12 check

Update the afids_latest link to point to the new version

    rm /pkg/afids/afids_latest
    ln -s ./afids_20161207 /pkg/afids/afids_latest
    
Python 2 Setup
------------

This is old directions for the python 2 setup. See next section for python 3

GeoCal depends on a number of python packages. We set up a virtual environment
for this.

Make sure pip is the system pip, so "which pip" returns /usr/bin/pip
(so you aren't already in a virtualenv). Then if you haven't already
installed virtualenv do:

    pip install --user virtualenv

(can skip if you already have this).

Make sure you are pointing to the afids installed libraries

    export GDAL_DRIVER_PATH=/pkg/afids/afids_latest/lib/gdalplugins
    export PATH=/pkg/afids/afids_latest/bin:${PATH}
    export LD_LIBRARY_PATH=/pkg/afids/afids_latest/lib64:/pkg/afids/afids_latest/lib:${LD_LIBRARY_PATH}
    export PYTHONPATH=/pkg/afids/afids_latest/lib/python2.7/site-packages:/pkg/afids/afids_latest/lib64/python2.7/site-packages:${PYTHONPATH}

Then

    cd /pkg/afids
    ~/.local/bin/virtualenv -p /usr/bin/python afids_pythonenv
    source afids_pythonenv/bin/activate
	unset PYTHONPATH

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

Python 3 Setup
------------

Make sure you are pointing to the afids installed libraries

    export GDAL_DRIVER_PATH=/pkg/afids/afids_latest/lib/gdalplugins
    export PATH=/pkg/afids/afids_latest/bin:${PATH}
    export LD_LIBRARY_PATH=/pkg/afids/afids_latest/lib64:/pkg/afids/afids_latest/lib:${LD_LIBRARY_PATH}
    export PYTHONPATH=/pkg/afids/afids_latest/lib/python3.5/site-packages:/pkg/afids/afids_latest/lib64/python3.5/site-packages:${PYTHONPATH}

Then set up virtual environment. This comes as part of the python
install (since 3.4 I think). *However* it turns out that the version
of virtual environment does not have the python-config script used by
Geocal for building. This got added fairly recently, see
https://github.com/pypa/virtualenv/issues/169. So for now, we need to
download an updated copy of virtualenv and use that instead. This will
likely go away with a future version of python:

    pip3 install virtualenv
    cd /pkg/afids
    /pkg/afids/afids_latest/bin/virtualenv afids_python3env_20160701
    ln -s afids_python3env_20160701 afids_python3env
    source afids_python3env/bin/activate
	unset PYTHONPATH
	
Need to link in the umfpack headers, or at least I couldn't figure out
a way to pass this to UMFPACK without linking here:

    mkdir -p afids_python3env/include
    ln -s /pkg/afids/afids_latest/include/umf* afids_python3env/include

Now install requirements. The various environment variables here are used
by different packages to know where to find things installed in
afids_latest rather than the system area:

    HDF5_DIR=/pkg/afids/afids_latest \
    BLAS=/pkg/afids/afids_latest/lib/libfblas.a \
    LAPACK=/pkg/afids/afids_latest/lib/libflapack.a \
    UMFPACK=/pkg/afids/afids_latest/lib/libumfpack.a \
    CFLAGS="-I/pkg/afids/afids_latest/include" \
    pip install -r ~/GeoCal/requirements.txt
    pip install -r ~/ecostress-level1/requirements.txt
	
There are GDAL python packages installed in /pkg/afids/afids_latest that we
want to use in the virtual environment. These aren't super easy to reinstall,
so we use the version already in afids, by doing a symbolic link:
    
	ln -s /pkg/afids/afids_latest/lib/python3.5/site-packages/GDAL-2.0.2-py3.5-linux-x86_64.egg /pkg/afids/afids_python3env_20171219/lib/python3.5/site-packages
    ln -s /pkg/afids/afids_latest/lib/python3.5/site-packages/easy-install.pth /pkg/afids/afids_python3env_20171219/lib/python3.5/site-packages
	
Similarly, we pull in opencv2:

    ln -s /pkg/afids/afids_latest/lib/python3.5/site-packages/cv2.cpython-35m-x86_64-linux-gnu.so /pkg/afids//afids_python3env_20171219/lib/python3.5/site-packages/

*Old text: Note that we can use the intel built verison of tensorflow, which has better
performance*

    pip install https://anaconda.org/intel/tensorflow/1.6.0/download/tensorflow-1.6.0-cp35-cp35m-linux_x86_64.whl
	
**NOTE:	 Actually, the intel version has terrible performance, it uses up tons
of memory and runs really slow on eco-tb1. Not sure what the issue is. But
instead, use tensorflow==1.5.0**
    
Bliss Setup
-----------
Just so we don't have two python installs, can do 

    pip install -r ~/ecostress-bliss/build/requirements.txt

This picks up what bliss needs.

(Note this is the same for python 2 and 3, don't need to change anything here.)

GeoCal Setup
------------

Make sure you are pointing to the afids installed libraries

    export GDAL_DRIVER_PATH=/pkg/afids/afids_latest/lib/gdalplugins
    export PATH=/pkg/afids/afids_latest/bin:${PATH}
    export LD_LIBRARY_PATH=/pkg/afids/afids_latest/lib64:/pkg/afids/afids_latest/lib:${LD_LIBRARY_PATH}
    export PYTHONPATH=/pkg/afids/afids_latest/lib/python3.5/site-packages:/pkg/afids/afids_latest/lib64/python3.5/site-packages:${PYTHONPATH}
    source /pkg/afids/afids_python3env/bin/activate

Then

    cd ~
    mkdir GeoCalBuild/build
    cd GeoCalBuild/build
    /home/smyth/GeoCal/configure --prefix=/pkg/afids/geocal_20160203 \
       THIRDPARTY=/pkg/afids/afids_latest --enable-maintainer-mode \
       --with-afids=/pkg/afids/afids_latest
    make -j 12 all && make install && make -j 12 check && make -j 12 installcheck

Setup file
----------
Create a setup file /pkg/afids/afids_pythonenv/

    export GDAL_DRIVER_PATH=/pkg/afids/afids_latest/lib/gdalplugins
    export PATH=/pkg/afids/afids_latest/bin:${PATH}
    export LD_LIBRARY_PATH=/pkg/afids/afids_latest/lib64:/pkg/afids/afids_latest/lib:${LD_LIBRARY_PATH}
    VIRTUAL_ENV_DISABLE_PROMPT=t source /pkg/afids/afids_pythonenv/bin/activate
    source /pkg/afids/geocal_latest/setup_afids_python.sh



