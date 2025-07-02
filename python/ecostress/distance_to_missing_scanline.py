import numpy as np


def find_center_of_missing_scan(dq):
    # takes in a data_quality_matrix, which for ECOSTRESS is of size
    # (5632, 5400). However, this code can work with any size key
    # assumptions here is that there are 8 consecutive bad pizels that
    # repeats every 128 pixels.  this code returns a scalar, which is
    # the index [between -.5 and 127.5] along there 5632 dimension
    # specifying where the center of the missing scanline is the .5 on
    # the index is necessary between with 8 bad pixels, then the
    # midpoint (median) of the bad band pixel is not an integer note
    # that this returned scalar is in python 0-based indexing.

    # find the size of the dimension perpendicular to the missing scan
    # columns
    dsize = dq.shape[0]

    # convert matrix to 0 (good data) or 1 (all bad data). Sum across
    # the rows (dimension perpendicular to scanline) to form a vector
    # of size 5632.  each element of binary_dq_vector is the total
    # number of bad pixel for that particular row
    binary_dq_matrix = dq > 0
    binary_dq_vector = np.sum(binary_dq_matrix, 1)

    # make a filtering mask of length 5632, consisting of zeros,
    # except for a band of eight 1's every 128 pixels apart by default
    # this mask has the band of 1's centered at -.5 (in modulo 128
    # arithmetics)
    filter_mask = np.zeros(
        [
            dsize,
        ]
    )
    for index in range(dsize):
        # compute the distance from the center of -.5 in modulo 128
        # arithmetics
        distance_from_center = np.mod(index - (-0.5), 128)
        if distance_from_center > 128 / 2:
            distance_from_center = 128 - distance_from_center

        if distance_from_center <= 4:
            filter_mask[index] = 1

    # iterate through and find the center index of the missing
    # scanline for THIS particular scene the key here to to shift the
    # filter_mask from 1-128 and then take the dot product of this
    # filter_mask against binary_dq_vector the true center index is
    # where this dot product is at a maximum
    best_center_so_far = -1
    best_center_so_far_dot_value = -1
    for index in range(128):
        current_filter_mask = shift_filter_mask_x_pixel(filter_mask, index)
        current_dot_value = np.dot(current_filter_mask, binary_dq_vector)

        # update best values so far if the current dot value exceeds
        # best so far
        if current_dot_value > best_center_so_far_dot_value:
            best_center_so_far_dot_value = current_dot_value
            best_center_so_far = -0.5 + index

    return best_center_so_far


def shift_filter_mask_x_pixel(filter_mask, x):
    # take in a vector of length L, shift the content of all elements
    # over by x amount. The function *wraps around* at the end of the
    # array example, let a = [0, 1, 2, 0,
    # 3]. shift_filter_mask_x_pixel(a , 1) = [3, 0, 1, 2, 0]

    fsize = filter_mask.size
    shifting_index = np.array(range(fsize))
    shifting_index = np.mod(shifting_index - x, fsize)
    shifted_filter_mask = filter_mask[shifting_index]

    return shifted_filter_mask


def is_within_x_pixel_of_missing_scanline(x_index, missing_scan_center_index, width=20):
    # shape of dataset is (5632, 5400). The data repeats every 128
    # bands in the 5632 direction.  takes in an index, and then says
    # with it is too close (within *width* pixels) of the edge
    # requires a missing_scan_center_index, which is a number [between
    # -1 and 127] specifying where the center of the missing scanline
    # is

    distance_from_center = np.mod(x_index - missing_scan_center_index, 128)
    if distance_from_center > 128 / 2:
        distance_from_center = distance_from_center - 128

    is_within_x_pixel = False
    if abs(distance_from_center) <= width + 4:
        is_within_x_pixel = True

    return is_within_x_pixel


__all__ = [
    "is_within_x_pixel_of_missing_scanline",
    "find_center_of_missing_scan",
]
