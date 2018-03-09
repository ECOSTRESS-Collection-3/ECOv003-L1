#include "ecostress_igc_collection.h"
#include "ecostress_serialize_support.h"
using namespace Ecostress;

template<class Archive>
void EcostressIgcCollection::serialize(Archive & ar, const unsigned int version)
{
  ar & BOOST_SERIALIZATION_BASE_OBJECT_NVP(IgcArray);
}

ECOSTRESS_IMPLEMENT(EcostressIgcCollection);

// See base class for description.
void EcostressIgcCollection::print(std::ostream& Os) const
{
  Os << "EcostressIgcCollection:\n"
     << "  Number of images: " << number_image() << "\n"
     << "  Images:\n";
  for(int i = 0; i < number_image(); ++i)
    Os << "    " << title(i) << "\n";
  Os << "  Parameter:\n";
  blitz::Array<double, 1> p = parameter_subset();
  std::vector<std::string> pname = parameter_name_subset();
  for(int i = 0; i < p.rows(); ++i)
    Os << "    " << pname[i] << ": " << p(i) << "\n";
}
