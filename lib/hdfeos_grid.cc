#include "hdfeos_grid.h"
#include <geocal/geocal_exception.h>
#include <geocal/ogr_coordinate.h>
#include <geocal/coordinate_converter.h>
#include <geocal/map_info.h>
#include <geocal/ostream_pad.h>
#include <boost/make_shared.hpp>
using namespace Ecostress;
using namespace GeoCal;

//-------------------------------------------------------------------------
/// Constructor, open an existing grid.
//-------------------------------------------------------------------------

HdfEosGrid::HdfEosGrid(const boost::shared_ptr<HdfEosFileHandle>& Fhandle,
		       const std::string& Grid_name)
: fhandle_(Fhandle),
  gname_(Grid_name),
  compression_code(-1),
  deflate_level(-1)
{
  gid_ = HE5_GDattach(Fhandle->file_id(), Grid_name.c_str());
  if(gid_ == -1)
    throw Exception("Trouble opening grid " + Grid_name);
  long xdim, ydim;
  double ulc[2], lrc[2];
  HE5_GDgridinfo(gid_, &xdim, &ydim, ulc, lrc);
  int projcode, zonecode, spherecode;
  double projparm[15];
  HE5_GDprojinfo(gid_, &projcode, &zonecode, &spherecode, projparm);
  // projcode 0 is a special case
  boost::shared_ptr<CoordinateConverter> cconv;
  if(projcode == 0) {
    cconv = boost::make_shared<GeodeticConverter>();
    // The coordinates are in DMS, convert to just degrees
    ulc[0] = HE5_EHconvAng(ulc[0], HE5_HDFE_DMS_DEG);
    ulc[1] = HE5_EHconvAng(ulc[1], HE5_HDFE_DMS_DEG);
    lrc[0] = HE5_EHconvAng(lrc[0], HE5_HDFE_DMS_DEG);
    lrc[1] = HE5_EHconvAng(lrc[1], HE5_HDFE_DMS_DEG);
  } else { 
    auto sref = boost::make_shared<OGRSpatialReference>();
    sref->importFromUSGS(projcode, zonecode, projparm, spherecode);
    auto owrap = boost::make_shared<OgrWrapper>(sref);
    cconv = boost::make_shared<OgrCoordinateConverter>(owrap);
  }
  int origincode;
  herr_t status = HE5_GDorigininfo(gid_, &origincode);
  if(status == -1)
    throw Exception("Call to HE5_GDorigininfo failed");
  if(origincode != HE5_HDFE_GD_UL)
    throw Exception("Only support HE5_HDFE_GD_UL origin code");
  minfo = MapInfo(cconv, ulc[0], ulc[1], lrc[0], lrc[1], xdim, ydim);
  // We don't have a size before calling this function, so just make
  // large buffers
  char fieldlist[1024*10];
  int rank[320];
  hid_t ntype[320];
  int nflds = HE5_GDinqfields(gid_, fieldlist, rank, ntype);
  if(nflds == -1)
    throw Exception("Call to HE5_GDinqfields failed");
  int st = 0;
  for(int i = 0; i < 1024*10; ++i) {
    if(fieldlist[i] == ',') {
      field_name_.push_back(std::string(&fieldlist[st], i-st));
      st = i+1;
    }
    if(fieldlist[i] == '\0') {
      field_name_.push_back(std::string(&fieldlist[st], i-st));
      break;
    }
  }
}

//-------------------------------------------------------------------------
/// Constructor, create a grid with the given map info.
//-------------------------------------------------------------------------

HdfEosGrid::HdfEosGrid(const boost::shared_ptr<HdfEosFileHandle>& Fhandle,
		       const std::string& Grid_name,
		       const GeoCal::MapInfo& Minfo,
		       int Compression_type, int Deflate_level)
: fhandle_(Fhandle),
  minfo(Minfo),
  gname_(Grid_name),
  compression_code(Compression_type),
  deflate_level(Deflate_level)
{
  // Sphere code here is WGS 84.
  int projcode, zonecode = -1, spherecode = 12;
  double projparm[15] = {0.0};
  double ulc[2], lrc[2];
  ulc[0] = minfo.ulc_x();
  ulc[1] = minfo.ulc_y();
  lrc[0] = minfo.lrc_x();
  lrc[1] = minfo.lrc_y();
  if(dynamic_cast<const GeodeticConverter*>(minfo.coordinate_converter_ptr().get())) {
    // The coordinates are in degrees, convert to DMS
    ulc[0] = HE5_EHconvAng(ulc[0], HE5_HDFE_DEG_DMS);
    ulc[1] = HE5_EHconvAng(ulc[1], HE5_HDFE_DEG_DMS);
    lrc[0] = HE5_EHconvAng(lrc[0], HE5_HDFE_DEG_DMS);
    lrc[1] = HE5_EHconvAng(lrc[1], HE5_HDFE_DEG_DMS);
    projcode=0;
  } else {
    // We could add support for other Ogr coordinates pretty easily,
    // but right now we have no need to this so just skip this
    throw Exception("Currently only support GeodeticConverter");
  }
  gid_ = HE5_GDcreate(Fhandle->file_id(), Grid_name.c_str(), minfo.number_x_pixel(),
		      minfo.number_y_pixel(), ulc, lrc);
  if(gid_ == -1)
    throw Exception("Trouble creating grid " + Grid_name);
  herr_t status = HE5_GDdefproj(gid_, projcode, zonecode, spherecode, projparm);
  if(status == -1)
    throw Exception("Call to HE5_GDdefproj failed");
  status = HE5_GDdeforigin(gid_, HE5_HDFE_GD_UL);
  if(status == -1)
    throw Exception("Call to HE5_GDdefproj failed");
}

//-------------------------------------------------------------------------
/// Convert from the DMS format to standard decimal degrees
//-------------------------------------------------------------------------

double HdfEosGrid::dms_to_deg(double dms)
{
  return HE5_EHconvAng(dms, HE5_HDFE_DMS_DEG);
}

//-------------------------------------------------------------------------
/// Convert from the DMS format to standard decimal degrees
//-------------------------------------------------------------------------

double HdfEosGrid::deg_to_dms(double deg)
{
  return HE5_EHconvAng(deg, HE5_HDFE_DEG_DMS);
}

void HdfEosGrid::close()
{
  if(gid_ != -1)
    HE5_GDdetach(gid_);
  gid_ = -1;
}

//-------------------------------------------------------------------------
/// Add field.
//-------------------------------------------------------------------------

void HdfEosGrid::add_field_uchar(const std::string& Name)
{
  hsize_t tiledims[2];
  tiledims[0] = minfo.number_y_pixel();
  tiledims[1] = minfo.number_x_pixel();
  herr_t status = HE5_GDdeftile(gid_, HE5_HDFE_TILE, 2, tiledims);
  if(status == -1)
    throw Exception("Call to HE5_GDdeftile failed");
  int compparm[1];
  compparm[0]=deflate_level;
  status = HE5_GDdefcomp(gid_, compression_code, compparm);
  if(status == -1)
    throw Exception("Call to HE5_GDdefcomp failed");
  status = HE5_GDdeffield(gid_, Name.c_str(), const_cast<char*>("YDim,XDim"), NULL,
			  H5T_NATIVE_UCHAR, 0);
  if(status == -1)
    throw Exception("Call to HE5_GDdeffield failed");
  field_name_.push_back(Name);
}

//-------------------------------------------------------------------------
/// Add field.
//-------------------------------------------------------------------------

void HdfEosGrid::add_field_float(const std::string& Name)
{
  hsize_t tiledims[2];
  tiledims[0] = minfo.number_y_pixel();
  tiledims[1] = minfo.number_x_pixel();
  herr_t status = HE5_GDdeftile(gid_, HE5_HDFE_TILE, 2, tiledims);
  if(status == -1)
    throw Exception("Call to HE5_GDdeftile failed");
  int compparm[1];
  compparm[0]=deflate_level;
  status = HE5_GDdefcomp(gid_, compression_code, compparm);
  if(status == -1)
    throw Exception("Call to HE5_GDdefcomp failed");
  status = HE5_GDdeffield(gid_, Name.c_str(), const_cast<char*>("YDim,XDim"), NULL,
			  H5T_NATIVE_FLOAT, 0);
  if(status == -1)
    throw Exception("Call to HE5_GDdeffield failed");
  field_name_.push_back(Name);
}
  

void HdfEosGrid::print(std::ostream& Os) const
{
  GeoCal::OstreamPad opad(Os, "    ");
  Os << "HdfEosGrid\n"
     << "  Filename: " << file_handle()->file_name() << "\n"
     << "  Grid:     " << gname_ << "\n"
     << "  Mapinfo:\n";
  opad << map_info() << "\n";
  opad.strict_sync();
}
