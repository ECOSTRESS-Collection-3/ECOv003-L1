These are fixtures used by pytest.

Altough these files can be directly imported, normally you instead list them on
conftest.py as a pytest_plugins. This is just a pytest convention, fixtures listed there
are automatically included in all the tests without needing to explicitly import them.
