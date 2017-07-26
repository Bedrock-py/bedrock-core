
############################################
#                                          #
#    Filter – Interface Specifications     #
#                                          #
############################################

#FILENAME MUST MATCH CLASSNAME

#must include these relative imports
from bedrock.dataloader.utils import Filter

#must return the same nme as the class listed below
def get_classname():
    return 'TweetDocument'

#must inherit from Filter
class TweetDocument(Filter):

    def __init__(self):
        super(TweetDocument, self).__init__()

        #name to be used for UI display
        self.name = 'Twitter'

        #description for UI display
        self.description = 'Converts documents into a term-frequency matrix and associated documents.'

        #type of the filter: {extract, convert, add}
        self.type = 'extract'

        #stage of processing during which the filter is used: {before, after}
        self.stage = 'before'

        #type of input this filter can be applied to: {String, Numeric}
        self.input = 'String'

        #list of output documents that are generated as a result of this filter
        self.outputs = ['documents.txt','dictionary.txt','matrix.mtx']

        #specifications for UI parameters
        self.parameters_spec = [{ "name" : "Limit", "attrname" : "limit", "value" : "", "type" : "input" }]

        #possible field names to be used for quick identification of potential applications
        self.possible_names = ['tweet']


    #must include an check function with these inputs
    #this function is used to determine if this filter can be applied to the sample data
    #name: the name of the field in the original data
    #sample: a sample item to use for testing
    def check(self, name, sample):
        ...
        #return boolean for whether or not this filter applies to the sample
        return True/False



    #EXAMPLE OF EXTRACT FILTER

    #must include an apply function with this input
    #this function applies the filter to the provided src
    #conf: a dictionary, fields are specified below
    def apply(self, conf):
        ...
        #extract filters must return a matrix specification (details can be found below)
        return matrix


    #EXAMPLE OF ADD FILTER

    def apply(self, conf):
        ...
        return ??


    #EXAMPLE OF CONVERT FILTER

    def apply(self, conf):
        ...
        return ??



############################################
#                                          #
#          matrix specifications           #
#                                          #
############################################

matrix = {
        #datetime for point of creation
        "created": "2015-02-23 22:34:39.818160",
        #filters used in the creation of the matrix
        "filters": {
          #empty dictionaries indicate no use of filters on that field
          "Petal length": {},
          "Petal width": {},
          "Sepal length": {},
          "Sepal width": {}
        },
        #unique id for the location of the matrix
        "id": "27651d66d4cf4375a75208d3482476ac",
        #type of the matrix: {csv, mtx}
        "mat_type": "csv",
        #user-provided name of the generated matrix
        "name": "iris_matrix",
        #list of the output files associated with the matrix
        "outputs": [
          "features_original.txt", #a new-line delimited file containing the original field names in the matrix
          "features.txt",#a new-line delimited file containing the user-provided field names for the matrix
          "matrix.csv" #the numeric matrix
        ],
        #absolute path for the location of the  matrix files on the host
        "rootdir": "/var/www/analytics-framework/dataloader/data/caa1a3105a22477f8f9b4a3124cd41b6/27651d66d4cf4375a75208d3482476ac/",
        #unique id for the source from which this matrix was generated
        "src_id": "caa1a3105a22477f8f9b4a3124cd41b6"
}
