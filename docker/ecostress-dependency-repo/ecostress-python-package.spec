Summary: This is the extra packages that ecostress-level1 depends on
Name: ecostress-python-package
Version: 1.0
Release: 1.el%{rhel}
License: Various
Group: Applications/Engineering
URL: http://numeric.scipy.org/
Source0: tensorflow-1.14.0-cp37-cp37m-linux_x86_64.whl
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Requires: python3-afids 

# Turn off the brp-python-bytecompile script, this fails on centos7
%global __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib[^[:space:]]*/brp-python-bytecompile[[:space:]].*$!!g')

%description
This is a number of python packages installed in /opt/afids_support
for ecostress-level1 support. We use to track each python package
separately, but this tends to be a lot of work without much of a
point. We tend to update and install these packages all as one, so 
there no point in tracking each package. These are all standard pip
packages, nothing special expect we install in /opt/afids_support.

%prep

%build

%install
rm -rf $RPM_BUILD_ROOT
export PYTHONPATH=$RPM_BUILD_ROOT/opt/afids_support/lib/python3.7/site-packages
pip install --root=$RPM_BUILD_ROOT $RPM_SOURCE_DIR/tensorflow-1.14.0-cp37-cp37m-linux_x86_64.whl
pip install --root=$RPM_BUILD_ROOT cython xlrd tflearn
# Note, the build puts debug information into the various python
# packages that contains the BUILDROOT. By default, rpmbuild check for
# this and fails.  In this particular case, we want this debug
# information in anyways. We don't have the source of the packages
# installed, but the debug information can still be useful to know
# where we might have failed. So when we build, make sure to define
# QA_SKIP_BUILD_ROOT=1 before doing the rpmbuild.  export
# QA_SKIP_BUILD_ROOT=1

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
/opt/afids_support/bin
/opt/afids_support/lib/python3.7/site-packages

%changelog
* Wed Jun  3 2020 Smyth <smyth@macsmyth> - 1.0-1.el%{rhel}
- Initial build.

