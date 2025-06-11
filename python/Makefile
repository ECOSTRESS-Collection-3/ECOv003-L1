# Just some basic command collected together, so I don't need to
# remember these

# We generally want to install in editable mode, so make default
install:
	pip install --prefix=$(ECOSTRESSTOP) -e .

# Without editable mode
install2:
	pip install --prefix=$(ECOSTRESSTOP) .

# ------------------------------------------------------------------
# See notes in README_developer.md about the
# use of linters and type checkers.
#
# It is *not* considered an error to fail these, however the output of
# the linter and type checker can useful. We try to get all the errors
# fixed just to reduce the noise in the output. You can also often
# just silence errors for things that aren't worth fixing. We aren't
# required to make the linter or type checker happy - just to write
# python code that works. But it is mildly useful to have everything
# cleanly passing so we can see the occasional real thing that the
# linter or type checker finds.
#
# Also it isn't a requirement to match the format that ruff or other
# formater want. But it is pretty easy just to run the tools to get
# constistent code, so we tend to do that.
# ------------------------------------------------------------------

lint:
	ruff check ecostress test

lint-fix:
	ruff check --fix ecostress test

format:
	ruff format ecostress test

# Note that PYTHONPATH is required, at least as of pip 24.3.1. The py.typed file needed to
# tell mypy that our modules have types doesn't get translated through using
# editable mode of pip. This is an issue going back at least a few years that hasn't
# been addressed - see https://github.com/python/mypy/issues/13392. We work around this
# just by giving a explicit path to our source code skipping going through the installed
# version. This is only for type checking, all our other tests/check use the pip installed
# version.
mypy-simplier:
	PYTHONPATH=$(PWD) mypy ecostress

# This adds options to check for missing typing info. We usually want this
mypy:
	PYTHONPATH=$(PWD) mypy --disallow-untyped-defs ecostress

check:
	pytest -n 10 test


# Install micromamba
PLATFORM=linux
ARCH=64
MICROMAMBA_URL=https://github.com/mamba-org/micromamba-releases/releases/latest/download/micromamba-$(PLATFORM)-$(ARCH)

micromamba:
	wget -qO micromamba $(MICROMAMBA_URL) && chmod +x micromamba

AFIDS_PACKAGE_DIR=/ldata/smyth/afids-conda-package/afids-conda-channel
# We should perhaps create our own manifest file
AFIDS_ENV_FILE=$(AFIDS_PACKAGE_DIR)/../Manifest_linux.yml
ENV_DIR=$(PWD)/../../ecostress-env

Manifest_linux-modify.yml: $(AFIDS_ENV_FILE)
# We need to replace the local-channel line found in the spec file, since
# this is a hard coded path and isn't necessarily the same on this system
	( grep -B 1000 afids-conda-channel $< | grep -v afids-conda-channel ) > Manifest_linux-modify.yml
	echo "  - file://$(AFIDS_PACKAGE_DIR)" >> Manifest_linux-modify.yml
	( grep -A 1000 afids-conda-channel $< | grep -v afids-conda-channel ) >> Manifest_linux-modify.yml

create-env: micromamba Manifest_linux-modify.yml
	-rm -rf $(ENV_DIR)
	./micromamba create -y  -c $(AFIDS_PACKAGE_DIR) -f Manifest_linux-modify.yml -p $(ENV_DIR)
	./micromamba run -p $(ENV_DIR) conda env config vars set LANDSAT_ROOT=/opt/afids/data/landsat
	./micromamba run -p $(ENV_DIR) conda env config vars set ELEV_ROOT=/opt/afids/data/srtmL2_filled
	./micromamba run -p $(ENV_DIR) mamba -y install ruff mypy tensorflow scikit-learn git-annex
	./micromamba run -p $(ENV_DIR) pip install types-tensorflow

# conda env config vars set ECOSTRESSTOP=/ldata/smyth/ecostress-env
# conda env config vars set TAE_PATH=${ECOSTRESSTOP}/vicar_pdf:${TAE_PATH}
