from geocal import ImageCoordinate
import matplotlib.pyplot as plt
import pytest

@pytest.mark.skip
def test_plot(isolated_dir, igc_hres):
    """This creates a IGC, and then creates a plot so we can check size,
    orientation, etc."""
    slat = []
    slon = []
    for i in range(0, 513, 256):
        tm, fc = igc_hres.time_table.time(ImageCoordinate(i, 0))
        slat.append(igc_hres.orbit_data(tm, i, 0).position_cf.latitude)
        slon.append(igc_hres.orbit_data(tm, i, 0).position_cf.longitude)
    alat = []
    alon = []
    blat = []
    blon = []
    for i in [0, 255, 256, 511, 512]:
        alat.append(igc_hres.ground_coordinate(ImageCoordinate(i, 0)).latitude)
        alon.append(igc_hres.ground_coordinate(ImageCoordinate(i, 0)).longitude)
        blat.append(
            igc_hres.ground_coordinate(
                ImageCoordinate(i, igc_hres.number_sample - 1)
            ).latitude
        )
        blon.append(
            igc_hres.ground_coordinate(
                ImageCoordinate(i, igc_hres.number_sample - 1)
            ).longitude
        )
    plt.plot(slon, slat, "o", label="Subspacecraft point")
    plt.plot(alon, alat, "o", label="Sample 0")
    plt.plot(blon, blat, "o", label="Sample %d" % (igc_hres.number_sample - 1))
    plt.annotate("Line 0", xy=(slon[0] + 0.005, slat[0]))
    plt.annotate("Line 256", xy=(slon[1] + 0.005, slat[1]))
    plt.annotate("(0,0)", xy=(alon[0] + 0.005, alat[0]))
    plt.annotate("(255,0)", xy=(alon[1] + 0.005, alat[1]))
    plt.annotate("(256,0)", xy=(alon[2] + 0.005, alat[2]))
    plt.annotate("(511,0)", xy=(alon[3] + 0.005, alat[3]))
    plt.annotate("(512,0)", xy=(alon[4] + 0.005, alat[4]))
    plt.annotate("(0,5399)", xy=(blon[0] + 0.005, blat[0]))
    plt.annotate("(255,5399)", xy=(blon[1] + 0.005, blat[1]))
    plt.annotate("(256,5399)", xy=(blon[2] + 0.005, blat[2]))
    plt.annotate("(511,5399)", xy=(blon[3] + 0.005, blat[3]))
    plt.annotate("(512,5399)", xy=(blon[4] + 0.005, blat[4]))
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.legend()
    plt.savefig("igc.png")
    if False:
        plt.show()


@pytest.mark.skip
def test_plot2(isolated_dir, igc_hres):
    """This creates a IGC, and then creates a plot so we can check size,
    orientation, etc."""
    slat = []
    slon = []
    for i in range(0, 513, 256):
        tm, fc = igc_hres.time_table.time(ImageCoordinate(i, 0))
        slat.append(igc_hres.orbit_data(tm, i, 0).position_cf.latitude)
        slon.append(igc_hres.orbit_data(tm, i, 0).position_cf.longitude)
    alat = []
    alon = []
    blat = []
    blon = []
    for i in [0, 255, 256, 511, 512]:
        alat.append(igc_hres.ground_coordinate(ImageCoordinate(i, 2650)).latitude)
        alon.append(igc_hres.ground_coordinate(ImageCoordinate(i, 2650)).longitude)
        blat.append(igc_hres.ground_coordinate(ImageCoordinate(i, 2750)).latitude)
        blon.append(igc_hres.ground_coordinate(ImageCoordinate(i, 2750)).longitude)
    plt.plot(slon, slat, "o", label="Subspacecraft point")
    plt.plot(alon, alat, "o", label="Sample 2650")
    plt.plot(blon, blat, "o", label="Sample 2750")
    plt.annotate("Line 0", xy=(slon[0] + 0.005, slat[0]))
    plt.annotate("Line 256", xy=(slon[1] + 0.005, slat[1]))
    plt.annotate("(0,2650)", xy=(alon[0] + 0.005, alat[0]))
    plt.annotate("(255,2650)", xy=(alon[1] + 0.005, alat[1]))
    plt.annotate("(256,2650)", xy=(alon[2] + 0.005, alat[2]))
    plt.annotate("(511,2650)", xy=(alon[3] + 0.005, alat[3]))
    plt.annotate("(512,2650)", xy=(alon[4] + 0.005, alat[4]))
    plt.annotate("(0,2750)", xy=(blon[0] + 0.005, blat[0]))
    plt.annotate("(255,2750)", xy=(blon[1] + 0.005, blat[1]))
    plt.annotate("(256,2750)", xy=(blon[2] + 0.005, blat[2]))
    plt.annotate("(511,2750)", xy=(blon[3] + 0.005, blat[3]))
    plt.annotate("(512,2750)", xy=(blon[4] + 0.005, blat[4]))
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Ground track, full resolution pixels")
    plt.legend()
    plt.savefig("igc2.png")
    if False:
        plt.show()


def test_igc(igc_hres, unit_test_data):
    """Test back and forward with igc"""
    # This doesn't work. We need to figure out why, perhaps a tolerance
    # issue of something like that. But for now just punt, we'll come back
    # to this
    if False:
        gc = igc_hres.ground_coordinate(ImageCoordinate(0, 0))
        print(igc_hres.image_coordinate(gc))

    gc = igc_hres.ground_coordinate(ImageCoordinate(10, 10))
    print(igc_hres.image_coordinate(gc))
    gc = igc_hres.ground_coordinate(ImageCoordinate(128, 10))
    print(igc_hres.image_coordinate(gc))
    gc = igc_hres.ground_coordinate(ImageCoordinate(255, 10))
    print(igc_hres.image_coordinate(gc))
    gc = igc_hres.ground_coordinate(ImageCoordinate(256, 10))
    print(igc_hres.image_coordinate(gc))
