from .ecostress_igc_extension import *
from .misc import create_igccol
from test_support import *

def test_overlap(igc):
    '''Test calculating the overlap between scans'''
    assert igc.overlap() == pytest.approx(20.66, abs=1e-2)

# Don't normally run. This is a bit slow, and depends on real data that
# is only available on eco-scf2.
@skip
def test_match_overlap():
    '''Test matching the overlap between'''
    igccol = create_igccol(468,7)
    igc = igccol.image_ground_connection(0)
    for scan, ic1, ic2, ic2_match in igc.match_all_overlap():
        print(scan, ic1, ic2, ic2_match)
    
