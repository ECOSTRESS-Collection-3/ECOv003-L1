import pytest

def pytest_addoption(parser):
    parser.addoption("--run-slow", action="store_true",
                     help="run slow tests")

