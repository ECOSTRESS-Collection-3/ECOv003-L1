FROM ecostress/afids:1.28

MAINTAINER Mike Smyth Mike.M.Smyth@jpl.nasa.gov

# Packages we need
RUN yum install gcc gcc-c++ gsl-devel -y
ADD ecostress-dependency-repo /media/ecostress-dependency-repo
RUN cp /media/ecostress-dependency-repo/ecostress-dependency.repo /etc/yum.repos.d/
RUN yum install --enablerepo=ecostress-dependency ecostress-python-package -y
RUN rm -r /media/ecostress-dependency-repo


