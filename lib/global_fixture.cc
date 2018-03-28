#include "global_fixture.h"
#include <boost/test/unit_test.hpp>
#include <boost/filesystem.hpp>
#include <cstdlib>
using namespace Ecostress;

//-----------------------------------------------------------------------
/// Setup for all unit tests.
//-----------------------------------------------------------------------

GlobalFixture::GlobalFixture() 
{
  set_default_value();
}

//-----------------------------------------------------------------------
/// Return the directory aster mosaic data is in. If we don't have the
/// mosaic data, return an empty string to indicated this - tests can
/// use this to skip if the mosaic data isn't available.
//-----------------------------------------------------------------------

std::string GlobalFixture::aster_mosaic_dir() const
{
  if(boost::filesystem::is_directory("/data/smyth/AsterMosaic"))
    return "/data/smyth/AsterMosaic/";
  if(boost::filesystem::is_directory("/project/ancillary/ASTER/CAMosaic"))
    return "/project/ancillary/ASTER/CAMosaic/";
  return "";
}

//-----------------------------------------------------------------------
/// Return the directory landsat 7 data is in. If we don't have the
/// mosaic data, return an empty string to indicated this - tests can
/// use this to skip if the mosaic data isn't available.
//-----------------------------------------------------------------------

std::string GlobalFixture::landsat7_dir() const
{
  if(boost::filesystem::is_directory("/raid22/band5_VICAR"))
    return "/raid22/";
  if(boost::filesystem::is_directory("/project/ancillary/LANDSAT/band5_VICAR"))
    return "/project/ancillary/LANDSAT/";
  return "";
}
