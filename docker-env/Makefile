ECOSTRESS_VERSION=8.00
DOCKER_BASE_VERSION=20250214
AFIDS_CONDA_PACKAGE=/home/smyth/Local/afids-conda-package
ECOSTRESS_SOURCE=/home/smyth/Local/ecostress-level1
BASE_DOCKER=oraclelinux:8

# Location of various datasets, just used to run docker image (no impact on docker
# image itself)
ECOSTRESS_ANCILLARY=/project/ancillary
AFIDS_DATA_ELEV_ROOT=$(ECOSTRESS_ANCILLARY)/SRTM/srtm_v3_dem_L2
AFIDS_DATA_LWM=$(ECOSTRESS_ANCILLARY)/SRTM/srtm_v3_lwm
AFIDS_DATA_SPICEDATA=/pkg/afids/afids_latest/data/cspice
AFIDS_DATA_ORTHO=$(ECOSTRESS_ANCILLARY)/LANDSAT
ECOSTRESS_OSP_DIR=/project/test/ASTER/EndToEndTest/8.00/l1_osp_dir
ECOSTRESS_WORKDIR=/home/smyth/Local/ecostress-workdir
END_TO_END_DIR=/project/test/ASTER/EndToEndTest

# Include a Makefile.local to override things, if found
-include Makefile.local

# Create environment with base conda/geocal environment installed
create-base:
	docker run -t -d --cidfile=docker_run.id -v $(AFIDS_CONDA_PACKAGE):/home/afids-conda-package:z -v $(ECOSTRESS_SOURCE):/home/ecostress-level1:z $(BASE_DOCKER) /bin/bash
	-cp ../env/Makefile.local ../env/Makefile.local.backup
	docker exec $$(cat docker_run.id) bash --login -c "dnf install -y make csh wget && cd /home/ecostress-level1/env && cp /home/ecostress-level1/docker-env/env_makefile.local Makefile.local && make create-env && /home/ecostress-env/bin/conda init && mkdir -p /project/ancillary/srtm_v3_dem_L2 /project/ancillary/srtm_v3_lwm /project/ancillary/cspice /project/ancillary/ortho_lsat7 /project/ancillary/l1_osp_dir /home/ecostress-workdir && mkdir -p /pkg/afids/afids_latest/data && ln -s /project/ancillary/cspice /pkg/afids/afids_latest/data && ln -s /home/ecostress-env/data/vdev /pkg/afids/afids_latest/data && mkdir -p /project/ancillary/SRTM && ln -s /project/ancillary/srtm_v3_dem_L2 /project/ancillary/SRTM && ln -s /project/ancillary/srtm_v3_lwm /project/ancillary/SRTM && mkdir -p /opt/afids/data && ln -s /project/ancillary/cspice /opt/afids/data && rm Makefile.local"
	-mv ../env/Makefile.local.backup ../env/Makefile.local
	docker commit $$(cat docker_run.id) ecostress/conda-base:$(DOCKER_BASE_VERSION)
	docker container stop $$(cat docker_run.id)
	rm docker_run.id

create-ecostress:
	docker run -t -d --cidfile=docker_run.id -v $(ECOSTRESS_SOURCE):/home/ecostress-level1:z ecostress/conda-base:$(DOCKER_BASE_VERSION) /bin/bash
	docker exec $$(cat docker_run.id) bash --login -c "mkdir /home/ecostress-level1-build && cd /home/ecostress-level1-build && ../ecostress-level1/configure --prefix=/home/ecostress-env && make -j 20 all && make install && rm -r /home/ecostress-level1-build /home/afids-conda-package && ( echo 'will cite' | parallel --citation )"
	docker commit $$(cat docker_run.id) ecostress/ecostress-level1:$(ECOSTRESS_VERSION)
	docker container stop $$(cat docker_run.id)
	rm docker_run.id
	docker save ecostress/ecostress-level1:$(ECOSTRESS_VERSION) | pigz > ecostress-level1-docker-$(ECOSTRESS_VERSION).tar.gz

# Rule to start a interactive docker instance, just so I don't need to
# remember the syntax
docker-start:
	docker run -it -v $(AFIDS_CONDA_PACKAGE):/home/afids-conda-package:z -v $(ECOSTRESS_SOURCE):/home/ecostress-level1:z $(BASE_DOCKER) /bin/bash

# Start the base version, with conda/geocal installed
docker-start2:
	docker run -it -v $(ECOSTRESS_SOURCE):/home/ecostress-level1:z ecostress/conda-base:$(DOCKER_BASE_VERSION) /bin/bash

# Start with installed version
docker-start3:
	docker run -it --workdir /home/ecostress-workdir \
          -v $(AFIDS_DATA_ELEV_ROOT):/project/ancillary/srtm_v3_dem_L2:z \
          -v $(AFIDS_DATA_LWM):/project/ancillary/srtm_v3_lwm:z \
          -v $(AFIDS_DATA_SPICEDATA):/project/ancillary/cspice:z \
          -v $(AFIDS_DATA_ORTHO):/project/ancillary/ortho_lsat7:z \
          -v $(ECOSTRESS_OSP_DIR):/project/ancillary/l1_osp_dir:z \
          -v $(ECOSTRESS_WORKDIR):/home/ecostress-workdir:z \
          -v $(END_TO_END_DIR):/home/EndToEndTest:Z \
          ecostress/ecostress-level1:$(ECOSTRESS_VERSION) \
          /bin/bash --login

# When a failure occurs, can connect to the docker instance used in a rule
docker-connect:
	docker exec -it $$(cat docker_run.id) bash --login

# If we have a failure and want to start with a new container, this
# stops the old one and removes the docker_run.id file
docker-cleanup:
	docker container stop $$(cat docker_run.id)
	rm docker_run.id

ecostress-image-end-to-end-check:
	docker run -t --workdir /home/ecostress-workdir \
          -v $(AFIDS_DATA_ELEV_ROOT):/project/ancillary/srtm_v3_dem_L2:z \
          -v $(AFIDS_DATA_LWM):/project/ancillary/srtm_v3_lwm:z \
          -v $(AFIDS_DATA_SPICEDATA):/project/ancillary/cspice:z \
          -v $(AFIDS_DATA_ORTHO):/project/ancillary/ortho_lsat7:z \
          -v $(ECOSTRESS_OSP_DIR):/project/ancillary/l1_osp_dir:z \
          -v $(ECOSTRESS_WORKDIR):/home/ecostress-workdir:z \
          -v $(END_TO_END_DIR):/home/EndToEndTest:Z \
          ecostress/ecostress-level1:$(ECOSTRESS_VERSION) \
          /bin/bash --login -c /home/EndToEndTest/latest/end_to_end.sh

# When we have an ecostress image we want to save, run this
ecostress-image-save:
	docker save ecostress/ecostress-level1:$(ECOSTRESS_VERSION) | pigz > ecostress-level1-docker-$(ECOSTRESS_VERSION).tar.gz

ecostress-image-delivery:
	@echo "Note that this will ask for you username and password."
	@echo "this is the normal LDAP username and password we use for"
	@echo "many JPL logins. The username should already be in the"
	@echo "right group to have write privileges to the artifactory"
	docker tag ecostress/ecostress-level1:$(ECOSTRESS_VERSION) cae-artifactory.jpl.nasa.gov:16001/gov/nasa/jpl/ecostress/sds/pge/pge-eco-level-1:$(ECOSTRESS_VERSION)
	docker login cae-artifactory.jpl.nasa.gov:16001
	docker push cae-artifactory.jpl.nasa.gov:16001/gov/nasa/jpl/ecostress/sds/pge/pge-eco-level-1:$(ECOSTRESS_VERSION)
