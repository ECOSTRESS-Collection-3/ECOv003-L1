#define PYTHON_MODULE_NAME _swig_wrap
#include "geocal/python_lib_init.h"

extern "C" {
  INIT_TYPE INIT_FUNC(_ecostress_swig_array)(void);
  INIT_TYPE INIT_FUNC(_ecostress_dqi)(void);
  INIT_TYPE INIT_FUNC(_ecostress_camera)(void);
  INIT_TYPE INIT_FUNC(_ecostress_orbit)(void);
  INIT_TYPE INIT_FUNC(_ecostress_orbit_l0_fix)(void);
  INIT_TYPE INIT_FUNC(_ecostress_paraxial_transform)(void);
  INIT_TYPE INIT_FUNC(_ecostress_time_table)(void);
  INIT_TYPE INIT_FUNC(_ecostress_scan_mirror)(void);
  INIT_TYPE INIT_FUNC(_resampler)(void);
  INIT_TYPE INIT_FUNC(_ecostress_image_ground_connection)(void);
  INIT_TYPE INIT_FUNC(_ecostress_igc_collection)(void);
  INIT_TYPE INIT_FUNC(_ecostress_rad_apply)(void);
  INIT_TYPE INIT_FUNC(_ecostress_rad_average)(void);
  INIT_TYPE INIT_FUNC(_ecostress_band_to_band)(void);
  INIT_TYPE INIT_FUNC(_ground_coordinate_array)(void);
  INIT_TYPE INIT_FUNC(_simulated_radiance)(void);
  INIT_TYPE INIT_FUNC(_hdfeos_filehandle)(void);
  INIT_TYPE INIT_FUNC(_hdfeos_grid)(void);
  INIT_TYPE INIT_FUNC(_coordinate_convert)(void);
  INIT_TYPE INIT_FUNC(_geometric_model_image_handle_fill)(void);
}

static void module_init(PyObject* module)
{
  INIT_MODULE(module, "_ecostress_swig_array", INIT_FUNC(_ecostress_swig_array));
  INIT_MODULE(module, "_ecostress_dqi", INIT_FUNC(_ecostress_dqi));
  INIT_MODULE(module, "_ecostress_camera", INIT_FUNC(_ecostress_camera));
  INIT_MODULE(module, "_ecostress_orbit", INIT_FUNC(_ecostress_orbit));
  INIT_MODULE(module, "_ecostress_orbit_l0_fix", INIT_FUNC(_ecostress_orbit_l0_fix));
  INIT_MODULE(module, "_ecostress_paraxial_transform", INIT_FUNC(_ecostress_paraxial_transform));
  INIT_MODULE(module, "_ecostress_time_table", INIT_FUNC(_ecostress_time_table));
  INIT_MODULE(module, "_ecostress_scan_mirror", INIT_FUNC(_ecostress_scan_mirror));
  INIT_MODULE(module, "_resampler", INIT_FUNC(_resampler));
  INIT_MODULE(module, "_ecostress_image_ground_connection", INIT_FUNC(_ecostress_image_ground_connection));
  INIT_MODULE(module, "_ecostress_igc_collection", INIT_FUNC(_ecostress_igc_collection));
  INIT_MODULE(module, "_ecostress_rad_apply", INIT_FUNC(_ecostress_rad_apply));
  INIT_MODULE(module, "_ecostress_rad_average", INIT_FUNC(_ecostress_rad_average));
  INIT_MODULE(module, "_ecostress_band_to_band", INIT_FUNC(_ecostress_band_to_band));
  INIT_MODULE(module, "_ground_coordinate_array", INIT_FUNC(_ground_coordinate_array));
  INIT_MODULE(module, "_simulated_radiance", INIT_FUNC(_simulated_radiance));
  INIT_MODULE(module, "_hdfeos_filehandle", INIT_FUNC(_hdfeos_filehandle));
  INIT_MODULE(module, "_hdfeos_grid", INIT_FUNC(_hdfeos_grid));
  INIT_MODULE(module, "_coordinate_convert", INIT_FUNC(_coordinate_convert));
  INIT_MODULE(module, "_geometric_model_image_handle_fill", INIT_FUNC(_geometric_model_image_handle_fill));
}
