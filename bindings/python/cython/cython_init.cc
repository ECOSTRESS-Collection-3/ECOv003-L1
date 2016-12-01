#define PYTHON_MODULE_NAME _ecostress_level1
#define DO_CYTHON 1
#include "geocal/python_lib_init.h"

extern "C" {
  INIT_TYPE INIT_FUNC(cython_sample)(void);
  INIT_TYPE INIT_FUNC(cython_sample2)(void);
}

static void module_init(PyObject* module)
{
    PyObject *cython_list = PyList_New(0);
  INIT_MODULE(cython_list, "ecostress.cython_sample", INIT_FUNC(cython_sample));
  INIT_MODULE(cython_list, "ecostress.cython_sample2", INIT_FUNC(cython_sample2));
    PyObject *parent_module = PyImport_AddModule((char *)"ecostress");
    PyObject_SetAttrString(parent_module, "_cython_module_list", cython_list);
}
