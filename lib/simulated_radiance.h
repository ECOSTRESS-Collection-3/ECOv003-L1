#ifndef SIMULATED_RADIANCE_H
#define SIMULATED_RADIANCE_H
#include "ground_coordinate_array.h"
#include "geocal/raster_image.h"

namespace Ecostress {
/****************************************************************//**
  This is used to produce simulated radiance data. This is based on
  an underlying Map_projected_image (e.g., ASTER data), and we
  simulate what ecostress would see when viewing this data. The
  simulated data is like L1A_PIX data, except that it is still in
  whatever units the Map_projected_image is. A separate step is needed
  to convert this into DNs to make a proper L1A_PIX file.
*******************************************************************/

class SimulatedRadiance : public GeoCal::Printable<SimulatedRadiance> {
public:
  SimulatedRadiance(const boost::shared_ptr<GroundCoordinateArray>& Gca,
	    const boost::shared_ptr<GeoCal::RasterImage>& Map_projected_image, 
	    int Avg_fact = -1,
	    bool Read_into_memory = false,
	    double Fill_value = 0.0)
    : gca_(Gca), avg_factor_(Avg_fact),
      read_into_memory_(Read_into_memory), fill_value_(Fill_value),
      img_(Map_projected_image)
  { init(); }
  virtual ~SimulatedRadiance() {}

//-------------------------------------------------------------------------
/// Return underlying GroundCoordinateArray.
//-------------------------------------------------------------------------

  const boost::shared_ptr<GroundCoordinateArray>& ground_coordinate_array()
    const {return gca_;}

//-------------------------------------------------------------------------
/// Averaging factor to use with map_projected_image().
//-------------------------------------------------------------------------

  int avg_factor() const { return avg_factor_; }

//-------------------------------------------------------------------------
/// If true, read Map_projected_image completely into
/// memory. Otherwise we read as needed.
//-------------------------------------------------------------------------
  
  bool read_into_memory() const { return read_into_memory_; }

//-------------------------------------------------------------------------
/// Fill value to use when we are outside map_projected_image().
//-------------------------------------------------------------------------
  
  double fill_value() const {return fill_value_;}

//-------------------------------------------------------------------------
/// Underlying radiance data.
//-------------------------------------------------------------------------
  
  const boost::shared_ptr<GeoCal::RasterImage>& map_projected_image() const
  { return img_; }

  virtual void print(std::ostream& Os) const;
private:
  boost::shared_ptr<GroundCoordinateArray> gca_;
  int avg_factor_;
  bool read_into_memory_;
  double fill_value_;
  boost::shared_ptr<GeoCal::RasterImage> img_;
  boost::shared_ptr<GeoCal::RasterImage> img_avg_;
  void init();
  SimulatedRadiance() {}
  friend class boost::serialization::access;
  template<class Archive>
  void serialize(Archive & ar, const unsigned int version);
  template<class Archive>
  void save(Archive & ar, const unsigned int version) const;
  template<class Archive>
  void load(Archive & ar, const unsigned int version);
};
}

BOOST_CLASS_EXPORT_KEY(Ecostress::SimulatedRadiance);
#endif

