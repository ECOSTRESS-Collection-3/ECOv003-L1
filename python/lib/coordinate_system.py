import numpy as np

# This has the coordinate systems from the ATB in explicit form. We don't
# actually use these in the production code, but it is good for testing to
# have everything explicitly.

# Note that "optics" is *not* the same as the "camera coordinate system" we
# use. For a strictly nadir orientation, out z in camera coordinates points
# down, the "optics" points up. x points in the velocity direction in both
# cases. y finishes the coordinate system in both cases. I believe this gives:

m_camera_to_optics = np.matrix([[1,  0, 0, 0],
                                [0, -1, 0, 0],
                                [0,  0, -1, 0],
                                [0,  0, 0, 1]])

# Note, I'm not if that means that band separation I have in my camera model
# is going the wrong way or not, we may have a sign error

# Equation 4 in ATB
x_o_optics = np.array([0.8, -0.022, 0.104])

# Equation 3 in ATB
m_optics_to_10 = np.matrix([[0, 1,  0, x_o_optics[0]],
                           [1, 0,  0, x_o_optics[1]],
                           [0, 0, -1, x_o_optics[2]],
                           [0, 0,  0, 1]])

# Equation 6 in ATB
x_o_10 = np.array([4.9902, -0.050, 0.3825])

# Equation 5 in ATB
m_10_to_ef = np.matrix([[1, 0, 0, x_o_10[0]],
                       [0, 1, 0, x_o_10[1]],
                       [0, 0, 1, x_o_10[2]],
                       [0, 0 , 0, 1]])

# Equation 8 in ATB
x_o_ef = np.array([11.138, 0, -1.685])

# Equation 7 in ATB
m_ef_to_jem = np.matrix([[1,  0,  0, x_o_ef[0]],
                        [0, -1,  0, x_o_ef[1]],
                        [0,  0, -1, x_o_ef[2]],
                        [0,  0,  0, 1]])

# Equation 10 in ATB
x_o_a = np.array([10.9359, -2.3365, 4.8506])

# Equation 9 in ATB
m_jem_to_a = np.matrix([[ 0, -1,  0, x_o_a[0]],
                       [-1,  0,  0, x_o_a[1]],
                       [ 0,  0, -1, x_o_a[2]],
                       [ 0,  0,  0, 1]])
