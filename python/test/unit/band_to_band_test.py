try:
    from ecostress_swig import *
except ImportError:
    raise RuntimeError("You need to install the ecostress swig code first. You can install just this by doing 'make install-swig-python'")
import geocal
from test_support import *

def test_band_to_band(isolated_dir, igc_hres, lwm, dn_fname, gain_fname):
    '''Test band to band registration'''
    # Check that we have initial misregistration
    igc_hres.band = EcostressImageGroundConnection.REF_BAND
    gp = igc_hres.ground_coordinate(ImageCoordinate(100,100))
    igc_hres.band = 2
    ic = igc_hres.image_coordinate(gp)
    assert abs(100 - ic.sample) > 10
    igc_hres.band = EcostressImageGroundConnection.REF_BAND
    rrad = EcostressRadApply(dn_fname, gain_fname, 2)
    # Create a model.
    scan_index = 10
    tplist = band_to_band_tie_points(igc_hres, scan_index, 2)
    m = geocal.QuadraticGeometricModel()
    m.fit_transformation(tplist)
    rradsub = geocal.SubRasterImage(rrad, scan_index * igc_hres.number_line_scan, 0,
                             igc_hres.number_line_scan,
                             igc_hres.number_sample)
    geocal.GdalRasterImage.save("b3_before.img", "VICAR", rradsub,
                         GdalRasterImage.Float64)
    refrad = EcostressRadApply(dn_fname, gain_fname,
                               EcostressImageGroundConnection.REF_BAND)
    refradsub = geocal.SubRasterImage(refrad, scan_index * igc_hres.number_line_scan,
                               0, igc_hres.number_line_scan,
                               igc_hres.number_sample)
    geocal.GdalRasterImage.save("b4.img", "VICAR", refradsub,
                         GdalRasterImage.Float64)
    # Set fill to 0, just because xvd doesn't like -9999. Real data has
    # -9999
    #fill_value = -9999
    fill_value = 0
    rbreg = geocal.GeometricModelImage(rradsub, m, igc_hres.number_line_scan,
                                igc_hres.number_sample, fill_value,
                                geocal.GeometricModelImage.NEAREST_NEIGHBOR)
    geocal.GdalRasterImage.save("b3.img", "VICAR", rbreg,
                                geocal.GdalRasterImage.Float64)
    
        
    
    
