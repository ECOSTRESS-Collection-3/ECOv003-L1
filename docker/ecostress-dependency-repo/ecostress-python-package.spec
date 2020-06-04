Summary: This is the extra packages that ecostress-level1 depends on
Name: ecostress-python-package
Version: 1.0
Release: 1.el%{rhel}
License: Various
Group: Applications/Engineering
URL: http://numeric.scipy.org/
Source0: tensorflow-1.14.0-cp37-cp37m-linux_x86_64.whl
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Requires: python3-afids python-package

# Turn off the brp-python-bytecompile script, this fails on centos7
%global __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib[^[:space:]]*/brp-python-bytecompile[[:space:]].*$!!g')
# For some reason the libraries from Pillow get tracked as a requirment,
# but not something that python-package supplies. Not sure why the
# disconnect, but filter these
%global __requires_exclude ^lib[a-z0-9]*-[a-z0-9]*\\.so\\..*$

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

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%exclude /opt/afids_support/bin/__pycache__/
%exclude /opt/afids_support/lib/python3.7/site-packages/__pycache__/
/opt/afids_support/bin/freeze_graph
/opt/afids_support/bin/markdown_py
/opt/afids_support/bin/runxlrd.py
/opt/afids_support/bin/saved_model_cli
/opt/afids_support/bin/tensorboard
/opt/afids_support/bin/tf_upgrade_v2
/opt/afids_support/bin/tflite_convert
/opt/afids_support/bin/toco
/opt/afids_support/bin/toco_from_protos
/opt/afids_support/lib/python3.7/site-packages/Keras_Preprocessing-*.dist-info/
/opt/afids_support/lib/python3.7/site-packages/Keras_Applications-*.dist-info/
/opt/afids_support/lib/python3.7/site-packages/Markdown-*.dist-info/
/opt/afids_support/lib/python3.7/site-packages/PIL/
/opt/afids_support/lib/python3.7/site-packages/Pillow-*.dist-info/
/opt/afids_support/lib/python3.7/site-packages/Pillow.libs/
/opt/afids_support/lib/python3.7/site-packages/Werkzeug-*.dist-info/
/opt/afids_support/lib/python3.7/site-packages/absl/
/opt/afids_support/lib/python3.7/site-packages/absl_py-*.dist-info/
/opt/afids_support/lib/python3.7/site-packages/astor-*.dist-info/
/opt/afids_support/lib/python3.7/site-packages/astor/
/opt/afids_support/lib/python3.7/site-packages/gast-*.dist-info/
/opt/afids_support/lib/python3.7/site-packages/gast/
/opt/afids_support/lib/python3.7/site-packages/google/protobuf/
/opt/afids_support/lib/python3.7/site-packages/grpc/
/opt/afids_support/lib/python3.7/site-packages/grpcio-*.dist-info/
/opt/afids_support/lib/python3.7/site-packages/keras_applications/
/opt/afids_support/lib/python3.7/site-packages/keras_preprocessing/
/opt/afids_support/lib/python3.7/site-packages/markdown/
/opt/afids_support/lib/python3.7/site-packages/pasta/
/opt/afids_support/lib/python3.7/site-packages/google_pasta-*.dist-info/
/opt/afids_support/lib/python3.7/site-packages/protobuf-*/
/opt/afids_support/lib/python3.7/site-packages/protobuf-*-nspkg.pth
/opt/afids_support/lib/python3.7/site-packages/tensorboard/
/opt/afids_support/lib/python3.7/site-packages/tensorboard-*.dist-info/
/opt/afids_support/lib/python3.7/site-packages/tensorflow/
/opt/afids_support/lib/python3.7/site-packages/tensorflow-*.dist-info/
/opt/afids_support/lib/python3.7/site-packages/tensorflow_estimator/
/opt/afids_support/lib/python3.7/site-packages/tensorflow_estimator-*.dist-info/
/opt/afids_support/lib/python3.7/site-packages/termcolor-*.dist-info/
/opt/afids_support/lib/python3.7/site-packages/termcolor.py
/opt/afids_support/lib/python3.7/site-packages/tests/
/opt/afids_support/lib/python3.7/site-packages/tflearn/
/opt/afids_support/lib/python3.7/site-packages/tflearn-*.dist-info/
/opt/afids_support/lib/python3.7/site-packages/werkzeug/
/opt/afids_support/lib/python3.7/site-packages/wrapt
/opt/afids_support/lib/python3.7/site-packages/wrapt-*.dist-info/
/opt/afids_support/lib/python3.7/site-packages/xlrd/
/opt/afids_support/lib/python3.7/site-packages/xlrd-*.dist-info/

%changelog
* Wed Jun  3 2020 Smyth <smyth@macsmyth> - 1.0-1.el%{rhel}
- Initial build.

