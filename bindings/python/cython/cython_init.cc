#include <Python.h>
#include <iostream>

// Python 2 and 3 do strings differently, so we have a simple macro to 
// keep from having lots of ifdefs spread around. See 
// https://wiki.python.org/moin/PortingExtensionModulesToPy3k for details on
// this.
#if PY_MAJOR_VERSION > 2
#define Text_FromUTF8(str) PyUnicode_FromString(str)
#else
#define Text_FromUTF8(str) PyString_FromString(str)
#endif

// Python 2 and 3 have different name for their cython init functions
#if PY_MAJOR_VERSION > 2
#define CYTHON_INIT_FUNC(S) PyInit_ ## S
#define CYTHON_INIT_TYPE PyObject *
#define CYTHON_INIT_MODULE init_extension_module3
#else
#define CYTHON_INIT_FUNC(S) init_ ## S
#define CYTHON_INIT_TYPE void
#define CYTHON_INIT_MODULE init_extension_module2
#endif

extern "C" {
#if PY_MAJOR_VERSION > 2
  PyObject * PyInit__ecostress_level1(void);
#else
  void init_ecostress_level1(void);
#endif
  CYTHON_INIT_TYPE CYTHON_INIT_FUNC(cython_sample)(void);
  CYTHON_INIT_TYPE CYTHON_INIT_FUNC(cython_sample2)(void);
}

#if PY_MAJOR_VERSION > 2
// Version for python 3
static void init_extension_module3(PyObject* package, const char *modulename,
				  PyObject * (*initfunction)(void)) {
  PyObject *module = initfunction();
  PyObject *module_dic = PyImport_GetModuleDict();
  PyDict_SetItem(module_dic, Text_FromUTF8(modulename), module);
  if(PyModule_AddObject(package, (char *)modulename, module)) {
    std::cerr << "Initialisation in PyImport_AddObject failed for module "
	      << modulename << "\n";
    return;
  }
  Py_INCREF(module);
}
#else 
// Version for python 2
static void init_extension_module2(PyObject* package, const char *modulename,
				  void (*initfunction)(void)) {
  PyObject *module = PyImport_AddModule((char *)modulename);
  if(!module) {
    std::cerr << "Initialisation in PyImport_AddModule failed for module "
	      << modulename << "\n";
    return;
  }
  if(PyModule_AddObject(package, (char *)modulename, module)) {
    std::cerr << "Initialisation in PyImport_AddObject failed for module "
	      << modulename << "\n";
    return;
  }
  Py_INCREF(module);
  initfunction();
}
#endif


// This next blob of code comes from 
// https://wiki.python.org/moin/PortingExtensionModulesToPy3k

struct module_state {
    PyObject *error;
};

#if PY_MAJOR_VERSION >= 3
#define GETSTATE(m) ((struct module_state*)PyModule_GetState(m))
#else
#define GETSTATE(m) (&_state)
static struct module_state _state;
#endif

static PyObject *
error_out(PyObject *m) {
    struct module_state *st = GETSTATE(m);
    PyErr_SetString(st->error, "something bad happened");
    return NULL;
}

static PyMethodDef ecostress_level1_methods[] = {
    {"error_out", (PyCFunction)error_out, METH_NOARGS, NULL},
    {NULL, NULL}
};

#if PY_MAJOR_VERSION >= 3

static int ecostress_level1_traverse(PyObject *m, visitproc visit, void *arg) {
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int ecostress_level1_clear(PyObject *m) {
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}


static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "_ecostress_level1",
        NULL,
        sizeof(struct module_state),
        ecostress_level1_methods,
        NULL,
        ecostress_level1_traverse,
        ecostress_level1_clear,
        NULL
};

#define INITERROR return NULL

PyObject *
PyInit__ecostress_level1(void)

#else
#define INITERROR return

void
init_ecostress_level1(void)
#endif
{
#if PY_MAJOR_VERSION >= 3
    PyObject *module = PyModule_Create(&moduledef);
#else
    PyObject *module = Py_InitModule("_ecostress_level1", ecostress_level1_methods);
#endif

    if (module == NULL) {
        std::cerr << "Initialization failed\n";
        INITERROR;
    }
    struct module_state *st = GETSTATE(module);

    st->error = PyErr_NewException("ecostress_level1.Error", NULL, NULL);
    if (st->error == NULL) {
        Py_DECREF(module);
        INITERROR;
    }

  CYTHON_INIT_MODULE(module, "_cython_sample", CYTHON_INIT_FUNC(cython_sample));
  CYTHON_INIT_MODULE(module, "_cython_sample2", CYTHON_INIT_FUNC(cython_sample2));

#if PY_MAJOR_VERSION >= 3
    return module;
#endif
};
