class L1bGeoGenerate(object):
    '''This generate a L1B geo output file from a given
    ImageGroundConnection. I imagine we will modify this as time
    goes on, this is really just a placeholder.
    '''
    def __init__(self, igc, output_name):
        '''Create a L1bGeoGenerate with the given ImageGroundConnection
        and output file name. To actually generate, execute the 'run'
        command.'''
        self.igc = igc
        self.output_name = output_name
