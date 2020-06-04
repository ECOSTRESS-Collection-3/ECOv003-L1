FROM centos:7

MAINTAINER Mike Smyth Mike.M.Smyth@jpl.nasa.gov

ADD afids.iso /root/afids.iso
# Unless we run as a privileged docker, we can't use the loopback to
# mount the iso. So install xorriso as an alternative
RUN yum install epel-release -y
RUN yum repolist
RUN yum install xorriso -y
RUN xorriso -osirrox on -indev /root/afids.iso -extract / /media/AFIDS
RUN cp /media/AFIDS/afids-dvd.repo /etc/yum.repos.d/
RUN yum install --enablerepo=afids-dvd afids-full -y
RUN rm /root/afids.iso
RUN rm -r /media/AFIDS
