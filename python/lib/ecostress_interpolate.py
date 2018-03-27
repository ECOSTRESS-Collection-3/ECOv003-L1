import tflearn
import tensorflow as tf
import numpy as np
import h5py
import random
import params

from tflearn.layers.conv import conv_2d, max_pool_2d
from tflearn.layers.core import input_data, dropout, fully_connected
from tflearn.layers.estimator import regression

# This code came from Hai Nguyen. Code was originally from
# /home/hainguye/ECOSTRESS/interpolate.py. We have modified this lightly
# to clean up the interface a bit.
#f = './Data/ECOSTRESS_Simulated_L1B_Kansas_2014168_withDataQuality.h5'
#f = './Data/ECOSTRESS_Simulated_L1B_Socal_2012224_withDataQuality.h5'
#f = './Data/ECOSTRESS_Simulated_L1B_Kansas_2014168_withDataQuality.h5'







##  take a 5400x5400x5 array and read the mean and standard deviation for each of the 5 variables (T1...T5).
##  assumes that missing data are already coded as NaN
def get_mean_and_std( dat ):

    L = dat.shape[ 2 ]
    mu = np.zeros( [L, 1] )
    sigma = np.zeros( [L, 1] )

    for index in range( L ):
        mu[ index ]    = np.nanmean( dat[ :, :, index ] )
        sigma[ index ] = np.nanstd( dat[ :, :, index ] )
    
    normalizing_constants = dict()
    normalizing_constants[ 'mean' ] = mu
    normalizing_constants[ 'std' ] = sigma
    return normalizing_constants



def normalizeData( dat  ):
    # take a 5400x5400x5 raw array (not normalized with -9999 coding)
    # recode -9999 and -9998 into NaN
    # take the mean and std of each of the 5 layers (NaN excluded)
    # return a normalized 5400x5400x5 and a dict of mean and std
    
    ##  replace -9998 and -9999 with NaN
    dat[ dat[:] == -9999 ] = np.NaN
    dat[ dat[:] == -9998 ] = np.NaN

    
    # mean and std
    normalizing_constants = get_mean_and_std( dat )
    
    #normalize each layer by the mean and the std (convert to z-score)
    for index in range( 5 ):
        data = dat[ :, :, index ]
        data = ( data - normalizing_constants[ 'mean' ][ index ] )/normalizing_constants[ 'std' ][ index ]
        
        dat[ :, :, index ] = data
    
    return dat, normalizing_constants
    


def readData( h5_file  ):
    ## take a h5_file and return a 5400x5400x5 matrix of bands 1 to 5
    ## missing values are coded as -9998 and -9999
    
    variable_names = [ '/SDS/radiance_1', '/SDS/radiance_2', '/SDS/radiance_3', '/SDS/radiance_4', '/SDS/radiance_5' ]
    
    pipe = h5py.File( h5_file, "r") 
    S = pipe[  variable_names[ 0 ] ].shape
    
    dat = np.zeros( S + (5,) )
    for index in range( 5 ):
        data = pipe[  variable_names[ index ] ]
        dat[ :, :, index ] = data
    
    pipe.close()
    
    
    return dat 


def get_data_quality( h5_file, band = 0 ):
    #  takes a h5 file name and return the data quality mask (0 for normal, 1 for missing scanline, and 2 for bad data/packets)
    #  since python is 0-based, band number starts at 0. So band 0 and 4 would be missing
    
    pipe = h5py.File( h5_file, "r")
    
    #   in hdf file the band is 1-based. Adding 1 to correct for that
    band = band + 1;
    variable_path = '/SDS/data_quality_' + str( band );
    
    # making a hard copy instead of a reference
    mask = pipe[ variable_path ][:]
    
    pipe.close()
    
    return mask



    

#def get_3x3x3_grid( h5_pipe, center_row, center_col ):
    # given an open h5 pipe, get the 3x3x3 cube centered at center_row and center_col indices (by default, the edges are supposed to be excluded)
    # center_row and center_col are supposed to be in 0-based indexing
    
    #output = np.zeros( [3,3,3] )
    
    #for index = range( 1, 4 ):
    #    output[ index - 1, :, : ] = h5_pipe[ variable_names[ index ] ][ range( (center_row-1), (center_row+2) ), range( (center_col-1), (center_col+2) )]
    
    
    
def residualNet():

    tf.reset_default_graph()
    tflearn.init_graph(soft_placement=True)

    # training a convolutional neural net model
    convnet = input_data(shape=[None, 3, 3, 3], name='input')
    
    
    convnet = tflearn.conv_2d(convnet, 16, 1, regularizer='L2', weight_decay=0.0001)
    ##  residual layer block
    
    convnet = tflearn.residual_block(convnet, 10, 16)
    
    


    ##  one fully connected layer with 30 neurons
    convnet = fully_connected(convnet, 30, activation='relu')
    convnet = dropout(convnet, 0.8)

    ## final output layer (the prediction value)
    convnet = fully_connected(convnet, 1, activation='linear')
    convnet = regression(convnet, optimizer='adam', learning_rate=0.001, loss='mean_square', name='targets') # Using the default batch size, which is 64 (see http://tflearn.org/layers/estimator/)

    return convnet



    
def resNEXT():

    tf.reset_default_graph()
    tflearn.init_graph(soft_placement=True)

    # training a convolutional neural net model
    convnet = input_data(shape=[None, 3, 3, 3], name='input')
    
    
    convnet = tflearn.conv_2d(convnet, 8, 1, regularizer='L2', weight_decay=0.0001)
    ##  residual layer block
    
    convnet = tflearn.resnext_block(convnet, 5, 8, 8)
    
    
    convnet = tflearn.batch_normalization(convnet)
    convnet = tflearn.activation(convnet, 'relu')

    ##  one fully connected layer with 30 neurons
    convnet = fully_connected(convnet, 20, activation='relu')
    convnet = dropout(convnet, 0.8)

    ## final output layer (the prediction value)
    convnet = fully_connected(convnet, 1, activation='linear')
    convnet = regression(convnet, optimizer='adam', learning_rate=0.001, loss='mean_square', name='targets') # Using the default batch size, which is 64 (see http://tflearn.org/layers/estimator/)

    return convnet

    
    
def forwardNet( activation = params.activation_function, layer_size_1 = params.layer_size_1, layer_size_2 = params.layer_size_2 ):

    tf.reset_default_graph()
    tflearn.init_graph(soft_placement=True)

    # training a convolutional neural net model
    convnet = input_data(shape=[None, 3, 3, 3], name='input')
    

    ##  one fully connected layer with 30 neurons
    convnet = fully_connected(convnet, layer_size_1, activation= activation)
    convnet = dropout(convnet, 0.8)
    
    ##  one fully connected layer with 30 neurons
    convnet = fully_connected(convnet,  layer_size_2, activation= activation)
    convnet = dropout(convnet, 0.8)
    

    ## final output layer (the prediction value)
    convnet = fully_connected(convnet, 1, activation='linear')
    adam = tflearn.optimizers.Adam(learning_rate=0.001, beta1=0.99)
    convnet = regression(convnet, optimizer=adam, loss='mean_square', name='targets') # Using the default batch size, which is 64 (see http://tflearn.org/layers/estimator/)

    return convnet
    


def create_training_data( dataset, missing_mask, training_size, band_number ):
    #  dataset should be a 5400x5400x5 array for  bands 1 to 5. Missing_mask should be a 5400x5400 matrix with 1 for missing data due to missing scanlines or 2 due to missing packets
    # create a training data set x of size training_sizex3x3x3 and y of size training_sizex1
    # band_number is an argument (integer) of which variable to use as the response. Either 0 or 4.
    
    #dataset = readData( h5_file, normalize = True )
    #missing_mask = get_missing_scans( h5_file )
    
    training_x = np.zeros( [ training_size, 3, 3, 3 ] )
    training_y = np.zeros( [ training_size, 1 ] )
    
    counter = 0
    
    while counter < training_size:
        random_x_ind = random.randint( 1, dataset.shape[0] - 2 )
        random_y_ind = random.randint( 1, dataset.shape[1] - 2 )
        
        # skip this iteration if this is a missing scan line (no response data to train on) or missing packets
        if missing_mask[ random_x_ind, random_y_ind ] > 0:
            continue
        
        # skipping the layer on the edges due to the 3x3 grid. Grab the 3x3x3 array centered on the random (x,y) index
        
        grid_3x3x3 = dataset[ (random_x_ind - 1):(random_x_ind + 2 ), \
                              (random_y_ind - 1):(random_y_ind + 2 ), \
                              1:4 ]
        
        #  also skipping this iteration if there is missing (NaN) data in any cell of the 3x3x3 array
        total_nan_in_grid = np.sum( np.isnan( grid_3x3x3 ) )
        if total_nan_in_grid > 0:
            continue
        
        training_x[ counter, :, :, : ] = grid_3x3x3
        training_y[ counter ] = dataset[ random_x_ind, random_y_ind, band_number ]
        
        counter= counter + 1
    
    return training_x, training_y
    
    
def create_missingScanline_data( dataset, missing_mask ):
    #  dataset should be a 5400x5400x5 array for  bands 1 to 5. Missing_mask should be a 5400x5400 matrix with 1 for missing data due to missing scanlines and 2 for missing packets
    # create a dataset (just the Nx3x3x3 matrix for the predictor) at the locations where we have missing scanline. To be used for filling in the missing scanline
    # output is the testing_x (Nx3x3x3), x_colIndex, y_colIndex (for the indices into the matrix)
    
        
    #dataset = readData( h5_file, normalize = True )
    #missing_mask = get_missing_scans( h5_file )
    
    S = dataset.shape
    
    #########   getting a grip on how many missing scanline elements there are
    total_missing_elements = np.sum( missing_mask[ : ]  == 1 )
    
    testing_x = np.zeros(  [ total_missing_elements , 3, 3, 3 ] )
    x_colIndex = [] 
    y_colIndex = []
    
    counter = 0
    
    for row_index in range( 1, S[0] - 1 ):
        for col_index in range( 1, S[1] - 1 ):
        
            if missing_mask[ row_index, col_index ] == 1:
            
                grid_3x3x3 = dataset[ (row_index - 1):(row_index + 2 ), \
                                       (col_index - 1):(col_index + 2 ),\
                                        1:4 ]
        
                total_nan_in_grid = np.sum( np.isnan( grid_3x3x3 ) )
                
                ##  skip this observation if there is at least one NaN in the 3x3x3 predictor grid
                if total_nan_in_grid > 0:
                    continue
                    
                testing_x[ counter, :, :, : ] = grid_3x3x3
                x_colIndex.append(  row_index  )
                y_colIndex.append(  col_index  )
        
                counter= counter + 1            
    
    # 
    testing_x   = testing_x[ 0:counter, :, :, : ] 

                
    return testing_x, x_colIndex, y_colIndex


            
#def create_missingScanline_data_withY( dataset, missing_mask ):
#    #  dataset should be a 5400x5400x5 array for  bands 1 to 5. Missing_mask should be a 5400x5400 matrix with True for missing data due to missing scanlines
#    # create a dataset (just the Nx3x3x3 matrix for the predictor) at the locations where we have missing scanline. To be used for filling in the missing scanline
#    # output is the testing_x (Nx3x3x3), x_colIndex, y_colIndex (for the indices into the matrix)
#    
#        
#    #dataset = readData( h5_file, normalize = True )
#    #missing_mask = get_missing_scans( h5_file )
#    
#    S = dataset.shape
#    
#    #########   getting a grip on how many missing scanline elements there are
#    total_missing_elements = np.sum( missing_mask )
#    
#    testing_x = np.zeros(  [ total_missing_elements , 3, 3, 3 ] )
#    testing_y = np.zeros(  [ total_missing_elements , 1] )
#    
#    x_colIndex = [] 
#    y_colIndex = []
#    
#    counter = 0
#    
#    for row_index in range( 1, S[0] - 1 ):
#        for col_index in range( 1, S[1] - 1 ):
#        
#            if missing_mask[ row_index, col_index ] == True:
#            
#                grid_3x3x3 = dataset[ (row_index - 1):(row_index + 2 ), \
#                                       (col_index - 1):(col_index + 2 ),\
#                                        1:4 ]
#        
#                total_nan_in_grid = np.sum( np.isnan( grid_3x3x3 ) )
#                
#                ##  skip this observation if there is at least one NaN in the 3x3x3 predictor grid
#                if total_nan_in_grid > 0:
#                    continue
#                    
#                testing_x[ counter, :, :, : ] = grid_3x3x3
#                testing_y[ counter, 0 ] =       dataset[ row_index, col_index, 0 ]
#                
#                x_colIndex.append(  row_index  )
#                y_colIndex.append(  col_index  )
#        
#                counter= counter + 1            
#    
#    # 
#    testing_x   = testing_x[ 0:counter, :, :, : ] 
#    testing_y   = testing_y[ 0:counter, :  ] 
#
#                
#    return testing_x, x_colIndex, y_colIndex
            



def interpolate_missing_bands( dataset, data_quality ):
##  inputs:  dataset     : a 5325x5325x5 matrix of data for band 1 to 5
##           data_quality: a 5325x5325 matrix of data quality (0, 1, or 2). 0 indicates normal data, 1 indicates missnig scanline, 2 indicates missing packets.
##	NOTE:    scene size does not have be be 5325x5325. The code will detect the size based on the input dataset. The 3rd dimension of dataset does need to be 5 (5 bands)
##  outputs: prediction_matrices:  a list of 2 5325x5325 array containing band 1 and 5 data with most of the missing scanlines filled in
##           predicted_locations:  a 5325x5325 matrix containing 0 (original data) or 1 (interpolated value)
##           prediction_errors  :  a list of 2 scalars, containing the standard deviation for band 1 and 5, respectively.
        
    ###  normalize the data (zscore and replace -9998 and -9999 with NaN), return the normalizing constants (mean and std)
    dataset_normalized, normalizing_constants = normalizeData( dataset.copy()  )
    
    ##  make the testing dataset 
    testing_x, x_colIndex, y_colIndex = create_missingScanline_data( dataset_normalized, data_quality )
    
    # outputs
    prediction_matrices = []
    prediction_errors = []
    
    for response_index in (0,4):
    
        ##make the training dataset 
        training_x, training_y = create_training_data( dataset_normalized, data_quality, params.training_size, response_index )
        
        
        tf.reset_default_graph()
        tflearn.init_graph(soft_placement=True)
            
        model = tflearn.DNN( forwardNet() , tensorboard_dir='./logs')
        #model = tflearn.DNN( resNEXT() , tensorboard_dir='./logs')
        model.fit(training_x ,  training_y, n_epoch=10)
        
        
        testing_y = model.predict( testing_x )
        
        ##  predict the missing radiance at the missing locations and convert it back onto original scale
        prediction = dataset[ :, :, response_index ]
        
        testing_y_predict = model.predict( testing_x )
        testing_y_predict_original_scale = testing_y_predict * normalizing_constants[ 'std' ][ response_index ] + normalizing_constants[ 'mean' ][ response_index ]
        
        prediction[ x_colIndex, y_colIndex] = testing_y_predict_original_scale[ :, 0]
        
        
        training_y_predict = model.predict( training_x )
        error_std = np.std(training_y_predict - training_y  ) * normalizing_constants[ 'std' ][ response_index ]
        predicted_locations = np.zeros( prediction.shape )
        predicted_locations[ x_colIndex, y_colIndex] = 1
        
        # save the prediction and errors
        prediction_matrices.append( prediction )
        prediction_errors.append( error_std  )
    
    return prediction_matrices, predicted_locations, prediction_errors




