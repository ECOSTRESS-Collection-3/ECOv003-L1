#define PYTHON_MODULE_NAME _swig_wrap
#include "geocal/python_lib_init.h"

extern "C" {
  INIT_TYPE INIT_FUNC(_ecostress_camera)(void);
}

static void module_init(PyObject* module)
{
  INIT_MODULE(module, "_ecostress_camera", INIT_FUNC(_ecostress_camera));
}
