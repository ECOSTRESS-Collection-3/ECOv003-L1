import warnings
import pytest
import re

# ------------------------------------------
# Various markers we use throughout the tests
# ------------------------------------------

# Short hand for marking as unconditional skipping. Good for tests we
# don't normally run, but might want to comment out for a specific debugging
# reason.
skip = pytest.mark.skip

# Marker for long tests. Only run with --run-long
long_test = pytest.mark.long_test

# ------------------------------------------
# Based on markers, we skip tests
# ------------------------------------------


def pytest_addoption(parser):
    parser.addoption("--run-long", action="store_true", help="run long tests")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-long"):
        skip_long_test = pytest.mark.skip(reason="need --run-long option to run")
        for item in items:
            if "long_test" in item.keywords:
                item.add_marker(skip_long_test)


# ------------------------------------------
# Includes fixtures, made available to all tests.
# ------------------------------------------

pytest_plugins = [
    "fixtures.dir_fixture",
    "fixtures.igc_fixture",
    "fixtures.misc_fixture",
]
