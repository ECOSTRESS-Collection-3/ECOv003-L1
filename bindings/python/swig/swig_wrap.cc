#define PYTHON_MODULE_NAME _swig_wrap
#include "geocal/python_lib_init.h"

extern "C" {
  INIT_TYPE INIT_FUNC(_ecostress_swig_array)(void);
  INIT_TYPE INIT_FUNC(_ecostress_camera)(void);
  INIT_TYPE INIT_FUNC(_ecostress_paraxial_transform)(void);
  INIT_TYPE INIT_FUNC(_ecostress_time_table)(void);
  INIT_TYPE INIT_FUNC(_ecostress_scan_mirror)(void);
}

static void module_init(PyObject* module)
{
  INIT_MODULE(module, "_ecostress_swig_array", INIT_FUNC(_ecostress_swig_array));
  INIT_MODULE(module, "_ecostress_camera", INIT_FUNC(_ecostress_camera));
  INIT_MODULE(module, "_ecostress_paraxial_transform", INIT_FUNC(_ecostress_paraxial_transform));
  INIT_MODULE(module, "_ecostress_time_table", INIT_FUNC(_ecostress_time_table));
  INIT_MODULE(module, "_ecostress_scan_mirror", INIT_FUNC(_ecostress_scan_mirror));
}
