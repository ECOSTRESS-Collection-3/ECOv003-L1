# This defines fixtures that gives the paths to various directories with
# test data

import os
import pytest
from pathlib import Path
import sys

# Add source to path. For some reason pytest can miss this even if we
# have this installed editable.
sys.path.append(str(Path(os.path.dirname(__file__)).parent.parent))

@pytest.fixture(scope="function")
def unit_test_data():
    """Return the unit test directory"""
    yield Path(os.path.dirname(__file__)).parent.parent.parent / "unit_test_data"

# Changed test data in 6.00. For backwards testing, just use the 5.00
# version of these files, it is sufficient for testing
@pytest.fixture(scope="function")
def test_data():
    '''Determine the directory with the test data.'''
    if("end_to_end_test_data" in os.environ):
        tdata = Path(os.environ["end_to_end_test_data"]) / "5.00"
    else:
        # Location on eco-scf
        tdata = Path("/project/test/ASTER/EndToEndTest/5.00")
        if(not os.path.exists(tdata)):
            # Location on pistol
            tdata=Path("/data/smyth/ecostress-test-data/5.00")
        if(not os.path.exists(tdata)):
            pytest.skip("Don't have ecostress-test-data, so skipping test")
    if(os.path.exists(tdata)):
        yield tdata
    else:
        pytest.skip("Don't have ecostress-test-data, so skipping test")
    
@pytest.fixture(scope="function")
def vicar_path():
    '''Add vicar_pdf to TAE_PATH'''
    original_tae_path = os.environ["TAE_PATH"]
    os.environ["TAE_PATH"] = f"{Path(os.path.dirname(__file__)).parent.parent.parent / 'vicar_pdf'}:{original_tae_path}"
    yield
    os.environ["TAE_PATH"] = original_tae_path
