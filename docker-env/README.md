This is a simple Makefile for creating a docker image for delivery.

Note we directly build this in docker and then save the image. I had used Dockerfile with
docker build in the past, but it also seemed a bit convoluted with no real gain over just
creating directly which was simpler and more direct.

We have the base enviroment with conda/geocal separated from the ecostress-level1 build, just
because it seems like this will be a bit more stable and needed to create less frequently.
To build:

1. Edit any versions and paths in the Makefile.
2. make create-base to create ecostress/conda-base:$(DOCKER_BASE_VERSION)
3. make create-ecostress to create ecostress/ecostress-level1:$(ECOSTRESS_IMAGE_VERSION). 
   This also creates
   a tar file sbg-tir-l1-docker-$(SBG_VERSION).tar.gz that can be delivered
   (you can comment this part out if you don't want this). We use pigz to compress, because
   this runs in parallel and is much faster than gzip.
   
