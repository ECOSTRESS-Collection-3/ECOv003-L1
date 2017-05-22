try:
    from ecostress_swig import *
except ImportError:
    raise RuntimeError("You need to install the ecostress swig code first. You can install just this by doing 'make install-swig-python'")
from geocal import *
from test_support import *
import matplotlib.pyplot as plt

def test_plot(igc):
    '''This creates a IGC, and then creates a plot so we can check size,
    orientation, etc.'''
    slat = []
    slon = []
    for i in range(0, 513, 256):
        tm, fc = igc.time_table.time(ImageCoordinate(i,0))
        slat.append(igc.orbit_data(tm, 0).position_cf.latitude)
        slon.append(igc.orbit_data(tm, 0).position_cf.longitude)
    alat = []
    alon = []
    blat = []
    blon = []
    for i in [0,255,256,511,512]:
        alat.append(igc.ground_coordinate(ImageCoordinate(i, 0)).latitude)
        alon.append(igc.ground_coordinate(ImageCoordinate(i, 0)).longitude)
        blat.append(igc.ground_coordinate(ImageCoordinate(i, igc.number_sample-1)).latitude)
        blon.append(igc.ground_coordinate(ImageCoordinate(i, igc.number_sample-1)).longitude)
    plt.plot(slon, slat, 'o', label="Subspacecraft point")
    plt.plot(alon, alat, 'o', label="Sample 0")
    plt.plot(blon, blat, 'o', label="Sample %d" %  (igc.number_sample-1))
    plt.annotate('Line 0', xy=(slon[0] + 0.005,slat[0]))
    plt.annotate('Line 256', xy=(slon[1] + 0.005,slat[1]))
    plt.annotate('(0,0)', xy=(alon[0] + 0.005,alat[0]))
    plt.annotate('(255,0)', xy=(alon[1] + 0.005,alat[1]))
    plt.annotate('(256,0)', xy=(alon[2] + 0.005,alat[2]))
    plt.annotate('(511,0)', xy=(alon[3] + 0.005,alat[3]))
    plt.annotate('(512,0)', xy=(alon[4] + 0.005,alat[4]))
    plt.annotate('(0,5399)', xy=(blon[0] + 0.005,blat[0]))
    plt.annotate('(255,5399)', xy=(blon[1] + 0.005,blat[1]))
    plt.annotate('(256,5399)', xy=(blon[2] + 0.005,blat[2]))
    plt.annotate('(511,5399)', xy=(blon[3] + 0.005,blat[3]))
    plt.annotate('(512,5399)', xy=(blon[4] + 0.005,blat[4]))
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.legend()
    plt.savefig("igc.png")
    plt.show()
    
def test_igc(igc, unit_test_data):
    '''Test back and forward with igc'''
    gc = igc.ground_coordinate(ImageCoordinate(10,10))
    print(igc.image_coordinate(gc))
    gc = igc.ground_coordinate(ImageCoordinate(128,10))
    print(igc.image_coordinate(gc))
    gc = igc.ground_coordinate(ImageCoordinate(255,10))
    print(igc.image_coordinate(gc))
    gc = igc.ground_coordinate(ImageCoordinate(256,10))
    print(igc.image_coordinate(gc))
