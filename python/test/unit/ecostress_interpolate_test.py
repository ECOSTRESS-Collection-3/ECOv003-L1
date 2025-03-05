from .ecostress_interpolate import *
from test_support import *
import h5py
import numpy as np

@slow
def test_interpolate(isolated_dir, test_data):
    # Original test data, we will change this
    f = h5py.File(test_data + "ECOSTRESS_Simulated_L1B_Kansas_2014168_withDataQuality.h5")
    dataset = np.zeros((*f["/SDS/radiance_1"].shape, 5))
    dqi = np.zeros(dataset.shape)
    for b in range(5):
        dataset[:,:,b] = f["/SDS/radiance_%d" % (b+1)]
        dqi[:,:,b] = f["/SDS/data_quality_%d" % (b+1)]
    print("Done reading data")
    inter = EcostressInterpolate()
    prediction_matrices, predicted_locations, prediction_errors = inter.interpolate_missing_bands(dataset, dqi)
