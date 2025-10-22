# Install conda environment
# --------------------------------------
# Things the user can change. Note you can change this by creating a Makefile.local
# to set these variables

ECOSTRESS_VERSION=8.01

# Should we install the latest conda packages, or the "pixi.lock" set known to
# work (which will often lag the latest conda packages). Most of the time
# latest should work fine, but there might be the occasional breakage (e.g.,
# conda moves to a newer version of python and our various packages haven't
# been rebuilt yet the newer python, a python package update breaks
# something).
PIXI_LOCKED=yes

mkfile_dir := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
# Location of environment we create
ENV_DIR=$(abspath $(mkfile_dir)../../ecostress-build/build-pixi)

# Location of afids conda packages (you can check this out from
# git@github.jpl.nasa.gov:Cartography/afids-conda-package.git
CONDA_PACKAGE_DIR=$(abspath $(mkfile_dir)../../afids-conda-package/afids-conda-channel)

# Location of various datasets
ECOSTRESS_ANCILLARY=/project/ancillary
AFIDS_DATA_ELEV_ROOT=$(ECOSTRESS_ANCILLARY)/SRTM/srtm_v3_dem_L2
AFIDS_DATA_LWM=$(ECOSTRESS_ANCILLARY)/SRTM/srtm_v3_lwm
AFIDS_COPERNICUS_DEM=$(ECOSTRESS_ANCILLARY)/Copernicus/copdem_v1_L2
AFIDS_COPERNICUS_LWM=$(ECOSTRESS_ANCILLARY)/Copernicus/coplwm_v1_L2
AFIDS_DATA_SPICEDATA=/pkg/afids/afids_latest/data/cspice
AFIDS_DATA_ORTHO=$(ECOSTRESS_ANCILLARY)/LANDSAT
ECOSTRESS_OSP_DIR=/project/test/ASTER/EndToEndTest/8.00/l1_osp_dir
ECOSTRESS_TEST_DATA=/project/test/ASTER/EndToEndTest

# Include a Makefile.local to override things, if found
-include Makefile.local
# ---------------------------------------------------------------------------
# Past this point are the rules, shouldn't need to modify these
# ---------------------------------------------------------------------------

OS := $(shell uname -s)

ifeq ($(OS),Darwin)
  PIXI_LOCK_DIR:=$(mkfile_dir)/osx
else
  PIXI_LOCK_DIR:=$(mkfile_dir)/linux
endif

ifeq '$(PIXI_LOCKED)' 'yes'
$(ENV_DIR)/pixi.toml: $(PIXI_LOCK_DIR)/pixi.toml
	sed s"|fake-afids-conda-channel|$(CONDA_PACKAGE_DIR)|"g $< > $@

$(ENV_DIR)/pixi.lock: $(PIXI_LOCK_DIR)/pixi.lock
	sed s"|fake-afids-conda-channel|$(CONDA_PACKAGE_DIR)|"g $< > $@

PIXI_FILE_INSTALL= $(ENV_DIR)/pixi.toml $(ENV_DIR)/pixi.lock

PIXI_FILE_DEPEND=$(PIXI_LOCK_DIR)/pixi.toml $(PIXI_LOCK_DIR)/pixi.lock

PIXI_INSTALL_COMMAND= pixi install --frozen --manifest-path $(ENV_DIR) 
else
$(ENV_DIR)/pixi.toml: $(mkfile_dir)pixi.toml
	sed s"|fake-afids-conda-channel|$(CONDA_PACKAGE_DIR)|"g $< > $@

PIXI_FILE_INSTALL= $(ENV_DIR)/pixi.toml

PIXI_FILE_DEPEND=$(mkfile_dir)pixi.toml

PIXI_INSTALL_COMMAND= pixi install --manifest-path $(ENV_DIR) 

endif

PIXI_INSTALL_COMMAND+= && pixi run --manifest-path $(ENV_DIR) bash -c "\$$CONDA_PREFIX/bin/conda env config vars set AFIDS_DATA_ELEV_ROOT=$(AFIDS_DATA_ELEV_ROOT) AFIDS_DATA_LWM=$(AFIDS_DATA_LWM) AFIDS_DATA_SPICEDATA=$(AFIDS_DATA_SPICEDATA) SPICEDATA=$(AFIDS_DATA_SPICEDATA) AFIDS_DATA_ORTHO=$(AFIDS_DATA_ORTHO) AFIDS_COPERNICUS_DEM=$(AFIDS_COPERNICUS_DEM) AFIDS_COPERNICUS_LWM=$(AFIDS_COPERNICUS_LWM) LANDSAT_ROOT=$(AFIDS_DATA_ORTHO) ELEV_ROOT=$(AFIDS_DATA_ELEV_ROOT) ECOSTRESS_OSP_DIR=$(ECOSTRESS_OSP_DIR) ECOSTRESSTOP=\$$CONDA_PREFIX TAE_PATH=\$$CONDA_PREFIX/vicar_pdf:$${TAE_PATH} AFIDS_DATA=\$$CONDA_PREFIX/data AFIDS_VDEV_DATA=\$$CONDA_PREFIX/data/vdev ECOSTRESS_TEST_DATA=$(ECOSTRESS_TEST_DATA)"

$(ENV_DIR): $(PIXI_FILE_DEPEND)
	-rm -rf $(ENV_DIR)
	pixi init -c conda-forge -c $(CONDA_PACKAGE_DIR) $(ENV_DIR)
	rm $(ENV_DIR)/pixi.toml
	$(MAKE) $(PIXI_FILE_INSTALL)
	pixi config set --local run-post-link-scripts insecure --manifest-path $(ENV_DIR)
	$(PIXI_INSTALL_COMMAND)
	- cd $(ENV_DIR) && pixi task rm configure
	cd $(ENV_DIR) && pixi task add configure "$(abspath $(mkfile_dir)/../configure) --prefix=\$$CONDA_PREFIX --with-test-data=$(ECOSTRESS_TEST_DATA) --enable-maintainer-mode"

# Recreate the environment, deleting if already there
# ------------------------------------------------------------
recreate-env:
	-rm -rf $(ENV_DIR)
	$(MAKE) create-env

# Build the conda envirornment, if needed or out of date.
# ------------------------------------------------------------
create-env: $(ENV_DIR)

# Update lock files, from existing environment
# --------------------------------------------
update-lock:
	sed "s|$(CONDA_PACKAGE_DIR)|fake-afids-conda-channel|"g $(ENV_DIR)/pixi.toml > $(PIXI_LOCK_DIR)/pixi.toml
	sed "s|$(CONDA_PACKAGE_DIR)|fake-afids-conda-channel|"g $(ENV_DIR)/pixi.lock > $(PIXI_LOCK_DIR)/pixi.lock

# Create a pixi pack file, that can be used to recreate the environment.
# Useful to do when we make a delivery, so we have a copy of what is
# needed to create everything. Should have already created the ENV
# Note we can compress this, but we don't get much from that.
# This is a tar file of a bunch of compressed data, so compressing
# a second time really isn't needed.
# --------------------------------------------

pixi-pack:
	pixi-pack $(ENV_DIR) --output-file env-pixi-pack-$(ECOSTRESS_VERSION).tar
