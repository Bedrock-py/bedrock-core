
############################################
#                                          #
#   Analytic – Interface Specifications    #
#                                          #
############################################

#FILENAME MUST MATCH CLASSNAME

#must include these relative imports
from bedrock.analytics.utils import Algorithm 

#must return the same nme as the class listed below
def get_classname():
    return 'Kmeans'

#must inherit from Algorithm
class Kmeans(Algorithm):
    def __init__(self):
        super(Kmeans, self).__init__()

        #list of parameters that should be initialized
        self.parameters = ['numClusters']

        #list of input files required
        self.inputs = ['matrix.csv']

        #list of output files produced
        self.outputs = ['assignments.csv']

        #name used in the UI for display
        self.name ='KMeans'

        #type of algorithm: {Dimension Reduction, Clustering, Statistics}
        self.type = 'Clustering'

        #description used in the UI for display
        self.description = 'Performs K-means clustering on the input dataset.'

        #specifications for UI parameters
        self.parameters_spec = [ { "name" : "Clusters", "attrname" : "numClusters", "value" : 3, "type" : "input", "step": 1, "max": 15, "min": 1 }]


    #must include a compute function with at least a filepath as input
    #filepath: a dictionary of the necessary inputs files
    # for example: {'assignments.csv': {'rootdir': 'path/to/dir/containing/assignments.csv'}}
    # access like: assignments_path = inputs['assignments.csv'] ['rootdir'] + 'assignments.csv'
    def compute(self, filepath, **kwargs):
        #if output files are not written during the compute function, add them to the results dictionary
        #and the framework will write them to the appropriate location
        self.results = {'assignments.csv': self.clusters}

        #no return objects permitted
