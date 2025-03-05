from setuptools import setup

# Version moved so we have one place it is defined.
exec(open("ecostress/version.py").read())

# Namespace packages are a bit on the new side. If you haven't seen
# this before, look at https://packaging.python.org/guides/packaging-namespace-packages/#pkgutil-style-namespace-packages for a description of
# this.
setup(
    name='ecostress',
    version=__version__,
    description='ECOSTRESS',
    author='Mike Smyth, Veljko Jovanovic',
    author_email='mike.m.smyth@jpl.nasa.gov, veljko.m.jovanovic@jpl.nasa.gov',
    license='Apache 2.0',
    packages=['ecostress'],
    package_data={"*" : ["py.typed", "*.pyi"]},
    install_requires=[
        'numpy', 'scipy', 
    ],
)
