import tflearn
import tensorflow as tf
import numpy as np
import random
import os
import math
from ecostress_swig import *
from distance_to_missing_scanline import *

from tflearn.layers.conv import conv_2d, max_pool_2d
from tflearn.layers.core import input_data, dropout, fully_connected
from tflearn.layers.estimator import regression

# Turn off output from tflearn. Not clear how to do this directly, we
# actually looked into the tflearn to figure out how to do this
# monkeypatching. We use the environment variable TF_CPP_MIN_LOG_LEVEL which
# is suppose to control other tensorflow logging. We have logic in
# setup_ecostress.sh.in to set this is we are not in an interactive terminal,
# or of course people can set this in their environment directly.

def _on_batch_end(self, training_state, snapshot=False):
    # Skip printing
    pass

if("TF_CPP_MIN_LOG_LEVEL" in os.environ and int(os.environ["TF_CPP_MIN_LOG_LEVEL"]) > 0):
    tflearn.callbacks.CURSES_SUPPORTED = False
    tflearn.callbacks.TermLogger.on_batch_end = _on_batch_end

class EcostressInterpolate(object):
    def __init__(self, time_table,
                 training_size = 600000, layer_size_1 = 35,
                 layer_size_2 = 17, activation_function = 'LeakyReLU',
                 tensorboard_dir='./tensorboard',
                 grid_size=5,
                 seed = 1234):
        '''Initialize data. The directory tensorboard_dir is a scratch 
        directory, and should be something that we can create/write to.
        For repeatably results, there is a seed passed in. Set this to
        none if you want to use the current system time (so each run
        is different).'''
        self.training_size = training_size
        self.layer_size_1 = layer_size_1
        self.layer_size_2 = layer_size_2
        self.activation_function = activation_function
        self.tensorboard_dir = tensorboard_dir
        self.seed = seed
        self.time_table = time_table
        # We train on self.grid_size x self.grid_size data
        self.grid_size = grid_size
        self.grid_size_half = math.floor(self.grid_size / 2)
        
    def normalize_data(self, datain):
        '''Take a 5400x5400x5 raw array (not normalized with -9999 coding)
        recode -9999 and -9998 into NaN take the mean and std of each of
        the 5 layers (NaN excluded) return a normalized 5400x5400x5 and 
        a dict of mean and std.'''

        # Copy data, since we will modify it
        dat = datain.copy()
        ##  Replace filled data with NaN
        dat[dat < fill_value_threshold] = np.NaN
    
        # mean and std
        self.mu = np.zeros((dat.shape[2],))
        self.sigma = np.zeros((dat.shape[2],))
        for i in range(self.mu.shape[0]):
            self.mu[i] = np.nanmean(dat[:,:,i])
            self.sigma[i] = np.nanstd(dat[:,:,i])
    
        #normalize each layer by the mean and the std (convert to z-score)
        for i in range(dat.shape[2]):
            dat[:,:,i] = ((dat[ :,:,i] - self.mu[i])/ self.sigma[i])

        return dat
    
    def forward_net(self):
        # training a convolutional neural net model
        convnet = input_data(shape=[None, self.grid_size, self.grid_size, 3],
                             name='input')
    
        ##  one fully connected layer with 30 neurons
        convnet = fully_connected(convnet, self.layer_size_1,
                                  activation=self.activation_function)
        # Not used in latest version from Hai
        #convnet = dropout(convnet, 0.8)
    
        ##  one fully connected layer with 30 neurons
        convnet = fully_connected(convnet,  self.layer_size_2,
                                  activation=self.activation_function)
        # Not used in latest version from Hai
        #convnet = dropout(convnet, 0.8)
    
        ## final output layer (the prediction value)
        convnet = fully_connected(convnet, 1, activation='linear')
        adam = tflearn.optimizers.Adam(learning_rate=0.001, beta1=0.99)
        convnet = regression(convnet, optimizer=adam, loss='mean_square', name='targets') # Using the default batch size, which is 64 (see http://tflearn.org/layers/estimator/)

        return convnet
    
    def create_training_data(self, dataset, missing_mask, band_number ):
        '''dataset should be a 5400x5400x5 array for  bands 1 to 5. 
        Missing_mask should be a 5400x5400 matrix with 1 for missing
        data due to missing scanlines or 2 due to missing packets
        create a training data set x of size training_sizexgsxgsx3 and y of 
        size training_sizex1
        band_number is an argument (integer) of which variable to use 
        as the response. Either 0 or 4.'''
        training_x = np.zeros( [ self.training_size, self.grid_size, self.grid_size, 3 ] )
        training_y = np.zeros( [ self.training_size, 1 ] )
        counter = 0
        random.seed(self.seed)
        # Probably slow loop, we should come back to speed this up.
        
        # find the index [ between -.5 and 127.5] of where the center of the missing scanline is
        center_of_missing_scanline = find_center_of_missing_scan( missing_mask )
        
        while counter < self.training_size:
            random_x_ind = random.randint(self.grid_size_half,
                               dataset.shape[0] - 1 - self.grid_size_half)
            random_y_ind = random.randint(self.grid_size_half,
                               dataset.shape[1] - 1 - self.grid_size_half)
            # Skip this iteration if we are too close to the edge of a scan,
            # because the scan has a discontinuity in the radiance data
            # and shouldn't be used for training
            if(self.time_table.close_to_scan_edge(random_x_ind,
                                                  self.grid_size_half)):
                continue
            
            #  skip this iteration if the center of the point (random_x_ind) is not close to the missing scanline
            #  default definition of 'close' is 20 pixels.
            is_close_to_missing_scanline  = is_within_x_pixel_of_missing_scanline( random_x_ind, center_of_missing_scanline)
            if is_close_to_missing_scanline == False:
                continue
            
            # skip this iteration if this is a missing scan line
            # (no response data to train on) or missing packets
            if missing_mask[random_x_ind, random_y_ind, band_number] > 0:
                continue
            # skipping the layer on the edges due to the gsxgs grid.
            # Grab the gsxgsx3 array centered on the random (x,y) index
            # (where gs is the grid size, e.g. 3
            grid_gsxgsx3 = dataset[(random_x_ind - self.grid_size_half):(random_x_ind + 1 + self.grid_size_half ),
                            (random_y_ind - self.grid_size_half):(random_y_ind + 1 + self.grid_size_half ),
                                 1:4]
            #  also skipping this iteration if there is missing (NaN)
            # data in any cell of the gsxgsx3 array
            total_nan_in_grid = np.sum(np.isnan(grid_gsxgsx3))
            if total_nan_in_grid > 0:
                continue

            current_y = dataset[ random_x_ind, random_y_ind, band_number ]
            if np.isnan( current_y ):
                continue
           
            training_x[counter, :, :, :] = grid_gsxgsx3
            training_y[counter] = dataset[random_x_ind, random_y_ind,
                                          band_number]
        
            counter= counter + 1
        return training_x, training_y
    
    
    def create_missing_scan_line_data(self, dataset, missing_mask, band_number ):
        '''dataset should be a 5400x5400x5 array for  bands 1 to 5. 
        Missing_mask should be a 5400x5400 matrix with 1 for missing 
        data due to missing scanlines and 2 for missing packets
        create a dataset (just the Nxgsxgsx3 matrix for the predictor) 
        at the locations where we have missing scanline. To be used 
        for filling in the missing scanline output is the 
        testing_x (Nxgsxgsx3), x_colIndex, y_colIndex 
        (for the indices into the matrix)'''

        total_missing_elements = np.sum( missing_mask[:,:,band_number]  == DQI_STRIPE_NOT_INTERPOLATED)
        testing_x = np.zeros([total_missing_elements, self.grid_size, self.grid_size, 3])
        x_colIndex = [] 
        y_colIndex = []
        counter = 0
        for row_index in range( self.grid_size_half, dataset.shape[0] - self.grid_size_half):
            for col_index in range(self.grid_size_half, dataset.shape[1] - self.grid_size_half ):
                if missing_mask[row_index, col_index, band_number] == DQI_STRIPE_NOT_INTERPOLATED:
                    grid_gsxgsx3 = dataset[ (row_index - self.grid_size_half):(row_index + 1 + self.grid_size_half ), \
                                          (col_index - self.grid_size_half):(col_index + 1 + self.grid_size_half ),\
                                          1:4 ]
                    total_nan_in_grid = np.sum(np.isnan(grid_gsxgsx3))
                
                    ##  skip this observation if there is at least one
                    ## NaN in the gsxgsx3 predictor grid
                    if total_nan_in_grid > 0:
                        continue
                    testing_x[ counter, :, :, : ] = grid_gsxgsx3
                    x_colIndex.append(row_index)
                    y_colIndex.append(col_index)
                    counter= counter + 1            
    
        testing_x   = testing_x[0:counter, :, :, : ] 
        return testing_x, x_colIndex, y_colIndex

    def interpolate_missing_bands(self, dataset, data_quality, log = None):
        '''
inputs:  dataset     : a 5325x5325x5 matrix of data for band 1 to 5
         data_quality: a 5325x5325 matrix of data quality (0, 1, 2, or 3).
        
NOTE: scene size does not have be be 5325x5325. The code will
      detect the size based on the input dataset. The 3rd dimension
      of dataset does need to be 5 (5 bands)

outputs: prediction_matrices:  a list of 2 5325x5325 array containing 
             band 1 and 5 data with most of the missing scanlines filled in
         predicted_locations:  a 5325x5325 matrix containing 0 (original data) 
             or 1 (interpolated value)
         prediction_errors  :  a list of 2 scalars, containing the 
             standard deviation for band 1 and 5, respectively.
'''        
        # normalize the data (zscore and replace fill with NaN),
        # and fill in mu and sigma with mean and stddev
        dataset_normalized = self.normalize_data(dataset)
    
    
        # outputs
        prediction_matrices = []
        prediction_errors = []
        predicted_locations = []
        for response_index in (0,4):
            ##  make the testing dataset
            if(log):
                print("INFO:EcostressInterpolate:Working on band %d" % (response_index + 1), file=log)
                print("INFO:EcostressInterpolate:Creating missing scan line data", file=log)
            print("Working on band %d" % (response_index + 1))
            print("Creating missing scan line data")
            testing_x, x_colIndex, y_colIndex = \
               self.create_missing_scan_line_data(dataset_normalized, data_quality, response_index)
            ##make the training dataset 
            if(log):
                print("INFO:EcostressInterpolate:Creating training data", file=log)
            print("Creating training data")
            training_x, training_y = self.create_training_data(dataset_normalized, data_quality, response_index )
            if(log):
                print("INFO:EcostressInterpolate:Done creating training data", file=log)
            print("Done creating training data")
                
            tf.reset_default_graph()
            tflearn.init_graph(soft_placement=True, seed=self.seed)
            if(self.seed is not None):
                tf.set_random_seed(self.seed)
            
            model = tflearn.DNN(self.forward_net(),
                                tensorboard_dir=self.tensorboard_dir)
            model.fit(training_x , training_y, n_epoch=10, shuffle=False)
        
            testing_y = model.predict( testing_x )
        
            ##  predict the missing radiance at the missing locations
            ## and convert it back onto original scale
            prediction = dataset[ :, :, response_index ]
        
            testing_y_predict = model.predict( testing_x )
            testing_y_predict_original_scale = testing_y_predict * self.sigma[response_index] + self.mu[ response_index ]
            prediction[ x_colIndex, y_colIndex] = testing_y_predict_original_scale[ :, 0]
        
            training_y_predict = model.predict( training_x )
            error_std = np.std(training_y_predict - training_y  ) * self.sigma[ response_index]
            pred_locations = np.zeros( prediction.shape )
            pred_locations[ x_colIndex, y_colIndex] = 1
            # save the prediction and errors
            prediction_matrices.append( prediction )
            predicted_locations.append(pred_locations)
            prediction_errors.append( error_std  )
    
        return prediction_matrices, predicted_locations, prediction_errors

__all__ = ["EcostressInterpolate"]    
