# Install conda environment
# --------------------------------------
# Things the user can change. Note you can change this by creating a Makefile.local
# to set these variables

# Should we install the latest conda packages, or the "fixed" set known to
# work (which will often lag the latest conda packages). Most of the time
# latest should work fine, but there might be the occasional breakage (e.g.,
# conda moves to a newer version of python and our various packages haven't
# been rebuilt yet the newer python, a python package update breaks
# something).
CONDA_FIXED=yes

# Location of environment we create
ENV_DIR=$(HOME)/ecostress-env

# Location of afids conda packages (you can check this out from
# git@github.jpl.nasa.gov:Cartography/afids-conda-package.git
CONDA_PACKAGE_DIR=../../afids-conda-package/afids-conda-channel

# Location of various datasets
ECOSTRESS_ANCILLARY=/project/ancillary
AFIDS_DATA_ELEV_ROOT=$(ECOSTRESS_ANCILLARY)/SRTM/srtm_v3_dem_L2
AFIDS_DATA_LWM=$(ECOSTRESS_ANCILLARY)/SRTM/srtm_v3_lwm
AFIDS_DATA_SPICEDATA=/pkg/afids/afids_latest/data/cspice
AFIDS_DATA_ORTHO=$(ECOSTRESS_ANCILLARY)/LANDSAT
ECOSTRESS_OSP_DIR=/project/test/ASTER/EndToEndTest/8.00/l1_osp_dir

# Include a Makefile.local to override things, if found
-include Makefile.local
# ---------------------------------------------------------------------------
# Past this point are the rules, shouldn't need to modify these
# ---------------------------------------------------------------------------

ECOSTRESS_ENVIRONMENT_FILE=$(if $(filter $(CONDA_FIXED),yes), ecostress_environment_fixed.yml, ecostress_environment_latest.yml)

# Install micromamba
PLATFORM=linux
ARCH=64
MICROMAMBA_URL=https://github.com/mamba-org/micromamba-releases/releases/latest/download/micromamba-$(PLATFORM)-$(ARCH)

micromamba:
	wget -qO micromamba $(MICROMAMBA_URL) && chmod +x micromamba

$(ENV_DIR): micromamba $(MUSES_ENVIRONMENT_FILE)
	-rm -rf $(ENV_DIR)
	./micromamba create --override-channels --channel conda-forge --channel $(CONDA_PACKAGE_DIR) -y -f $(ECOSTRESS_ENVIRONMENT_FILE) -p $(ENV_DIR)
	./micromamba run -p $(ENV_DIR) conda env export --override-channels --channel conda-forge --channel $(CONDA_PACKAGE_DIR) > ecostress_environment_installed.yml
	eval "$$($(ENV_DIR)/bin/conda shell.bash hook)" && conda activate $(ENV_DIR) && conda env config vars set AFIDS_DATA_ELEV_ROOT=$(AFIDS_DATA_ELEV_ROOT) AFIDS_DATA_LWM=$(AFIDS_DATA_LWM) AFIDS_DATA_SPICEDATA=$(AFIDS_DATA_SPICEDATA) SPICEDATA=$(AFIDS_DATA_SPICEDATA) AFIDS_DATA_ORTHO=$(AFIDS_DATA_ORTHO) LANDSAT_ROOT=$(AFIDS_DATA_ORTHO) ELEV_ROOT=$(AFIDS_DATA_ELEV_ROOT) ECOSTRESS_OSP_DIR=$(ECOSTRESS_OSP_DIR) ECOSTRESSTOP=$(ENV_DIR) TAE_PATH=$(ENV_DIR)/vicar_pdf:$${TAE_PATH} AFIDS_DATA=$(ENV_DIR)/data AFIDS_VDEV_DATA=$(ENV_DIR)/data/vdev

# Recreate the environment, deleting if already there
# ------------------------------------------------------------
recreate-env:
	-rm -rf $(ENV_DIR)
	$(MAKE) create-env

# Build the conda envirornment, if needed or out of date.
# ------------------------------------------------------------
create-env: $(ENV_DIR)

