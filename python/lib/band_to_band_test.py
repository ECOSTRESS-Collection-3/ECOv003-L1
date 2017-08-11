try:
    from ecostress_swig import *
except ImportError:
    raise RuntimeError("You need to install the ecostress swig code first. You can install just this by doing 'make install-swig-python'")
from geocal import *
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
    # Create a model.
    tplist = band_to_band_tie_points(igc_hres, 0, 2)
    m = QuadraticGeometricModel()
    m.fit_transformation(tplist)
    # We'll need to add better handling for other scan index, but for
    # now just resample the first
    rrad = EcostressRadApply(dn_fname, gain_fname, 2)
    rradsub = SubRasterImage(rrad, 0, 0, igc_hres.number_line_scan,
                             igc_hres.number_sample)
    GdalRasterImage.save("b3_before.img", "VICAR", rradsub,
                         GdalRasterImage.Float64)
    refrad = EcostressRadApply(dn_fname, gain_fname,
                               EcostressImageGroundConnection.REF_BAND)
    refradsub = SubRasterImage(refrad, 0, 0, igc_hres.number_line_scan,
                               igc_hres.number_sample)
    GdalRasterImage.save("b4.img", "VICAR", refradsub,
                         GdalRasterImage.Float64)
    # Set fill to 0, just because xvd doesn't like -999. But we'll
    #rbreg = GeometricModelImage(rradsub, m, igc_hres.number_line_scan,
    #                           igc_hres.number_sample, -9999)
    rbreg = GeometricModelImage(rradsub, m, igc_hres.number_line_scan,
                                igc_hres.number_sample, 0)
    GdalRasterImage.save("b3.img", "VICAR", rbreg,
                         GdalRasterImage.Float64)
    
        
    
    
