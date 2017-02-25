#****************************************************************
#
# Copyright (c) 2015, Georgia Tech Research Institute
# All rights reserved.
#
# This unpublished material is the property of the Georgia Tech
# Research Institute and is protected under copyright law.
# The methods and techniques described herein are considered
# trade secrets and/or confidential. Reproduction or distribution,
# in whole or in part, is forbidden except by the express written
# permission of the Georgia Tech Research Institute.
#****************************************************************/

#FILENAME MUST MATCH CLASSNAME

############################################
#                                          #
# Visualization – Interface Specifications #
#                                          #
############################################

#must include these relative imports
from bedrock.visualization.utils import Visualization


#must return the same nme as the class listed below
def get_classname():
    return 'Linechart'

#must inherit from VisBase
class Linechart(Visualization):
    def __init__(self):
        super(Linechart, self).__init__()

        #list of input files required
        self.inputs = ['matrix.csv', 'features.txt', 'selected_features']

        #list of parameters that should be initialized
        self.parameters = ['matrix','features', 'selected_features']

        #possible field names to be used for quick identification of potential applications
        self.parameters_spec = []

        #name to be used for UI display
        self.name = 'Linechart'

        #description for UI display
        self.description = ''


    #must include an initialize function with these inputs
    #inputs: a dictionary of the necessary inputs files
    # for example: {'assignments.csv': {'rootdir': 'path/to/dir/containing/assignments.csv'}}
    # access like: assignments_path = inputs['assignments.csv'] ['rootdir'] + 'assignments.csv'
    def initialize(self, inputs):
        self.features = utils.load_features(inputs['features.txt']['rootdir'] + 'features.txt')
        self.matrix = utils.load_dense_matrix(inputs['matrix.csv']['rootdir'] + 'matrix.csv', names=self.features)
        self.selected_features = inputs['selected_features']


    #must include a create function with no inputs
    def create(self):
        ...
        #must return a dictionary with these keys:
        #  data: either the data itself or a script that displays the data
        #  type: a name to be used by the UI to either execute the script or create the visualization using the provided data
        #  id: a unique id for this visualization
        #  title: the title to display for the vis
        return {'data':script,'type':'linechart', 'id': vis_id, 'title': title}


#INCLUDE DETAILS ON ANGULAR DEPENDENCIES
