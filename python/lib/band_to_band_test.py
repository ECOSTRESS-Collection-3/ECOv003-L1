try:
    from ecostress_swig import *
except ImportError:
    raise RuntimeError("You need to install the ecostress swig code first. You can install just this by doing 'make install-swig-python'")
from geocal import *
from test_support import *

def test_band_to_band(isolated_dir, igc_hres, lwm):
    '''Test band to band registration'''
    # Check that we have initial misregistration
    igc_hres.band = EcostressImageGroundConnection.REF_BAND
    gp = igc_hres.ground_coordinate(ImageCoordinate(100,100))
    igc_hres.band = 3
    ic = igc_hres.image_coordinate(gp)
    assert abs(100 - ic.sample) > 10
    igc_hres.band = EcostressImageGroundConnection.REF_BAND
    # Create a model
    tplist = band_to_band_tie_points(igc_hres, 0, 3)
    m = QuadraticGeometricModel()
    m.fit_transformation(tplist)
    print(m)
    print(tplist.x)
    print(tplist.y)
    print(m.resampled_image_coordinate(ImageCoordinate(100,100)))
    print(m.original_image_coordinate(ImageCoordinate(100,100)))
    print(m.resampled_image_coordinate(ImageCoordinate(200,200)))
    print(m.original_image_coordinate(ImageCoordinate(200,200)))
    print(m.resampled_image_coordinate(ImageCoordinate(256,5300)))
    
          
    
    
