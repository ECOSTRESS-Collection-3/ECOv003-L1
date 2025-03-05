from ecostress.run_config import RunConfig


def test_parse(unit_test_data):
    """Test parsing a sample run config file."""
    config = RunConfig(
        str(unit_test_data / "SMAP_L1B_TB_SPS_RunConfig_20150228T224642376.xml")
    )
    assert (
        config["DynamicAncillaryFileGroup", "RFIParameters"]
        == "/ops/LOM/ANCILLARY/RFIParameters/RFIParameters_130901_v008.h5"
    )
    assert config.as_list("DynamicAncillaryFileGroup", "RFIParameters") == [
        "/ops/LOM/ANCILLARY/RFIParameters/RFIParameters_130901_v008.h5",
    ]
    assert config["DynamicAncillaryFileGroup", "SpiceAntennaAzimuth"] == [
        "/ops/LOM/PREPROCESSOR_OUT/ANTAZ/001/2015/02/28/smap_ar_1502282014_1502282059_v01.bc",
        "/ops/LOM/PREPROCESSOR_OUT/ANTAZ/001/2015/02/28/smap_ar_1502281929_1502282014_v01.bc",
        "/ops/LOM/PREPROCESSOR_OUT/ANTAZ/001/2015/02/28/smap_ar_1502282059_1502282144_v01.bc",
    ]
    assert config.as_list("DynamicAncillaryFileGroup", "SpiceAntennaAzimuth") == [
        "/ops/LOM/PREPROCESSOR_OUT/ANTAZ/001/2015/02/28/smap_ar_1502282014_1502282059_v01.bc",
        "/ops/LOM/PREPROCESSOR_OUT/ANTAZ/001/2015/02/28/smap_ar_1502281929_1502282014_v01.bc",
        "/ops/LOM/PREPROCESSOR_OUT/ANTAZ/001/2015/02/28/smap_ar_1502282059_1502282144_v01.bc",
    ]
