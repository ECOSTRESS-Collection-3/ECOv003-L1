from ecostress.l1a_pix_generate import L1aPixGenerate
from ecostress.exception import VicarRunException
import pytest
from loguru import logger


@pytest.mark.long_test
def test_l1a_pix_generate(isolated_dir, test_data, vicar_path):
    fvar = "80005_001_20150124T204250_0100_01.h5"
    l1a_bb = str(test_data / f"ECOSTRESS_L1A_BB_{fvar}.expected")
    l1a_raw = str(test_data / f"L1A_RAW_PIX_{fvar}.expected")
    l1_osp_dir = str(test_data / "l1_osp_dir")
    logger.add("test.log", level="DEBUG")
    l1apix = L1aPixGenerate(
        l1a_bb,
        l1a_raw,
        l1_osp_dir,
        "ECOSTRESS_L1A_PIX_" + fvar,
        "L1A_RAD_GAIN_" + fvar,
    )
    l1apix.run()


def test_l1a_pix_generate_failed(isolated_dir, test_data, vicar_path):
    fvar = "80005_001_20150124T204250_0100_01.h5"
    l1a_raw = str(test_data / f"L1A_RAW_PIX_{fvar}.expected")
    l1_osp_dir = str(test_data / "l1_osp_dir")
    logger.add("test.log", level="DEBUG")
    # Pass in bad file name, to make sure we correctly handle a failed
    # job.
    l1apix = L1aPixGenerate(
        "bad_bb_data",
        l1a_raw,
        l1_osp_dir,
        f"ECOSTRESS_L1A_PIX_{fvar}",
        f"L1A_RAD_GAIN_{fvar}",
    )
    with pytest.raises(VicarRunException):
        l1apix.run()
