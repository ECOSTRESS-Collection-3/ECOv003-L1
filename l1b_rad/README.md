Note that you can convert the radiance data to vicar format and view using
xvd by something like:

    for i in $(seq 1 5); do gdal_calc.py --type=Float32  -A HDF5:"pytest_tmp/test_l1b_rad_generate0/ECOSTRESS_L1B_RAD_80005_001_20150124T204251_0100_01.h5"://Radiance/radiance_$i --outfile=b$i.tif --calc="A*(A>0)" --NoDataValue=0; gdal_translate -of VICAR b$i.tif b$i.img; done
	
The gdal_calc.py converts HDF 5 to tif, converting the -9999 values to 0. For
some reason that isn't worth tracking down this fails if we go straight to
VICAR format with an error message. So we convert first to tif using 
gdal_calc.py, and then use gdal_translate to convert to VICAR. This doesn't
convert the SW band 6, we could add that if desired.
