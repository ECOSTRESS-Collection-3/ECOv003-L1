#include "global_fixture.h"
#include <boost/test/unit_test.hpp>
#include <cstdlib>
using namespace Ecostress;

//-----------------------------------------------------------------------
/// Setup for all unit tests.
//-----------------------------------------------------------------------

GlobalFixture::GlobalFixture() 
{
  set_default_value();
}

