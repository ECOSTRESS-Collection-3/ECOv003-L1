#ifndef GLOBAL_FIXTURE_H
#define GLOBAL_FIXTURE_H
#include <string>

namespace Ecostress {
/****************************************************************//**
  This is a global fixture that is available to all unit tests.
*******************************************************************/
class GlobalFixture {
public:
  GlobalFixture();
  virtual ~GlobalFixture() { /* Nothing to do now */ }
  std::string test_data_dir() const;
  std::string unit_test_data_dir() const;
  std::string aster_mosaic_dir() const;
private:
  void set_default_value();
};
}
#endif
