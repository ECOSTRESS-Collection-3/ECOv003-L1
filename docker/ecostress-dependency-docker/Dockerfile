FROM ecostress/afids:1.29

MAINTAINER Mike Smyth Mike.M.Smyth@jpl.nasa.gov

# Packages we need
# This fails, but it doesn't seem to matter. I think it is
# some other package trying to update util-linux, but the permissions
# are such that this can't be done in docker
RUN yum update util-linux -y; exit 0
RUN yum install gcc gcc-c++ gsl-devel parallel make libjpeg-devel libpng-devel expat-devel sqlite-devel openssl-devel fftw-devel -y
RUN yum install atlas-devel bzip2-devel curl-devel expat-devel fftw-devel fontconfig-devel freetype-devel gd-afids glibc-devel gmp-devel gsl-devel libX11-devel libXpm-devel libffi-devel libjpeg-turbo-devel libpng-devel libtiff-devel ncurses-devel openmotif-devel openssl-devel readline-devel suitesparse-devel tcl-devel tk-devel xz-devel zlib-devel -y
RUN mkdir -p /root/.parallel && touch /root/.parallel/will-cite
# Always point to geocal stuff. I *think* this is ok, we can
# reevaluate this if needed in the future
RUN ( echo export PATH=/opt/afids_support/bin:${PATH} > /etc/profile.d/geocal.sh ) && ( echo export LD_LIBRARY_PATH=/opt/afids_support/lib:/opt/afids_support/lib64:${LD_LIBRARY_PATH} >> /etc/profile.d/geocal.sh ) && (echo export PKG_CONFIG_PATH=/opt/afids_support/lib/pkgconfig:/opt/afids/lib/pkgconfig >> /etc/profile.d/geocal.sh) && ( echo source /opt/afids/setup_geocal.sh >> /etc/profile.d/geocal.sh )
ADD ecostress-dependency-repo /media/ecostress-dependency-repo
RUN cp /media/ecostress-dependency-repo/ecostress-dependency.repo /etc/yum.repos.d/
RUN yum install --enablerepo=ecostress-dependency ecostress-python-package -y
# Update the location of the larger datasets. These aren't actually used when
# running, but the unit tests etc. expect these to point to the right locations
RUN rm /opt/afids/data/srtmL2_filled && ln -s /srtm /opt/afids/data/srtmL2_filled
RUN rm -r /media/ecostress-dependency-repo


