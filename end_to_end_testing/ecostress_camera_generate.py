# This is a short python script that ingests the distortion data. This is really
# just a placeholder to give something kind of right, we'll replace this with
# a real camera model from bill Johnson

import pandas as pd
import numpy as np
import scipy
import math
from multipolyfit import multipolyfit
import ecostress
import geocal

# Note nothing actually changes here, I think the differences go into the
# actual ecostress camera model
# Original test data
if(False):
    inp = "FPA distortion20140522.xlsx"
    out1 = "cam_paraxial_20140522.xml"
    out2 = "camera_20140522.xml"
    focal_length = 425
    frame_to_sc_q = geocal.Quaternion_double(1,0,0,0)
# Updated camera model from Bill Johnson
if(True):
    inp = "FPA distortion20180208.xlsx"
    out1 = "cam_paraxial_20180208.xml"
    out2 = "camera_20180208.xml"
    focal_length = 427.5
    y_offset = 0
    y_scale = 1
    frame_to_sc_q = geocal.Quaternion_double(1,0,0,0)

df = pd.read_excel(inp, "Data", header = 0,
                   skiprows = [1,])
real = np.empty((df['Predicted X'].shape[0], 2))
pred = np.empty((df['Predicted X'].shape[0], 2))
field_angle = np.empty((df['Predicted X'].shape[0], 2))
pred[:,0] = df['Predicted X']
pred[:,1] = df['Predicted Y']
real[:,0] = df['Real X']
real[:,1] = df['Real Y']
field_angle[:,0] = df['X-Field']
field_angle[:,1] = df['Y-Field']

# Determine the largest error in using a 3rd order polynomial
pixel_size = 0.04 # In mm
deg = 3
mo = multipolyfit(real, pred[:,0], deg, model_out=True)
print("Real to predict x max error (pixel) ", 
    abs(np.array([(mo(*real[i,:]) - pred[i,0]) / pixel_size for i in range(real.shape[0])])).max())
mo = multipolyfit(real, pred[:,1], deg, model_out=True)
print("Real to predict y max error (pixel) ", 
    abs(np.array([(mo(*real[i,:]) - pred[i,1]) / pixel_size for i in range(real.shape[0])])).max())

mo = multipolyfit(pred, real[:,0], deg, model_out=True)
print("Predict to real x max error (pixel) ", 
    abs(np.array([(mo(*pred[i,:]) - real[i,0]) / pixel_size for i in range(real.shape[0])])).max())
mo = multipolyfit(pred, real[:,1], deg, model_out=True)
print("Predict to real y max error (pixel) ", 
    abs(np.array([(mo(*pred[i,:]) - real[i,1]) / pixel_size for i in range(real.shape[0])])).max())

# Print out powers so we know how to interpret the polynomial coefficients. 
t, powers = multipolyfit(pred, real[:,1], deg, powers_out=True)
print(powers)

# Create a EcostressParaxialTransform that fits this data.
tran = ecostress.EcostressParaxialTransform()
tran.real_to_par[0,:] = multipolyfit(real, pred[:,0], deg)
tran.real_to_par[1,:] = multipolyfit(real, pred[:,1], deg)
tran.par_to_real[0,:] = multipolyfit(pred, real[:,0], deg)
tran.par_to_real[1,:] = multipolyfit(pred, real[:,1], deg)
geocal.write_shelve(out1, tran)
cam = ecostress.EcostressCamera(focal_length, y_scale, y_offset, frame_to_sc_q)
cam.paraxial_transform = tran

# Fit camera focal length so we match x field angles
def x_field(real_x, real_y):
    q = cam.focal_plane_to_dcs(0, real_x, real_y)
    return math.degrees(math.atan2(q.R_component_2, q.R_component_4))

def y_field(real_x, real_y):
    q = cam.focal_plane_to_dcs(0, real_x, real_y)
    return math.degrees(math.atan2(q.R_component_3, q.R_component_4))

def x_field_func(focal_length):
    cam.focal_length = focal_length[0]
    res = np.empty((real.shape[0],))
    for i in range(res.shape[0]):
        res[i] = -field_angle[i,0] - x_field(real[i,0],real[i,1])
    return res

def y_field_func(x):
    cam.y_scale = x[0]
    cam.y_offset = x[1]
    res = np.empty((real.shape[0],))
    for i in range(res.shape[0]):
        res[i] = -field_angle[i,1] - y_field(real[i,0],real[i,1])
    return res

print(scipy.optimize.least_squares(x_field_func, (focal_length,)))
print(scipy.optimize.least_squares(y_field_func, (1,0)))
print(cam.focal_length)
print(cam.y_scale)
print(cam.y_offset)
print(x_field(5.07306, 3.09521))
print(y_field(5.07306, 3.09521))
print(-field_angle[51,:])
geocal.write_shelve(out2, cam)

# Check that we calculate the right values
print("Predict real x max error (pixel) ", 
      abs(np.array([(tran.real_to_paraxial(*real[i,:])[0] - pred[i,0]) / pixel_size for i in range(real.shape[0])])).max())
print("Predict real y max error (pixel) ", 
      abs(np.array([(tran.real_to_paraxial(*real[i,:])[1] - pred[i,1]) / pixel_size for i in range(real.shape[0])])).max())
print("Real to predict x max error (pixel) ", 
      abs(np.array([(tran.paraxial_to_real(*pred[i,:])[0] - real[i,0]) / pixel_size for i in range(real.shape[0])])).max())
print("Real to predict y max error (pixel) ", 
      abs(np.array([(tran.paraxial_to_real(*pred[i,:])[1] - real[i,1]) / pixel_size for i in range(real.shape[0])])).max())






