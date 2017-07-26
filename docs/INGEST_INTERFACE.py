
############################################
#                                          #
# Ingest Module – Interface Specifications #
#                                          #
############################################

#FILENAME MUST MATCH CLASSNAME

#must include these relative imports
from bedrock.dataloader.utils import Ingest

#must return the same nme as the class listed below
def get_classname():
    return 'Spreadsheet'

#must inherit from IngestModule
class Spreadsheet(Ingest):

    def __init__(self):
        super(Spreadsheet, self).__init__()

        #name to be used for UI display
        self.name = 'CSV/Microsoft Excel'

        #description for UI display
        self.description = 'Loads data from CSV or Microsft Excel spreadsheets.'

        #specifications for UI parameters
        self.parameters_spec = [{ "name" : "file", "value" : ".csv,.xls,.xlsx", "type" : "file" }]


    #must include an explore function with these inputs
    #this function is called with the user indicates a desire to see what is in a particular source
    #filepath: the absolute path to the directory where the original file is stored, e.g. the name.csv file
    def explore(self, filepath):
        ...
        #must return a list of schemas (the fields for which are detailed below) and an HTTP code
        return schemas, 200

    #must include an ingestfunction with these inputs
    #this function is calld when the user wants to generate a matrix from a particular source
    #posted_data: a dictionary, the fields for which are detailed below
    #src: a dictionary, the fields for which are detailed below
     def ingest(self, posted_data, src):
        ...
        #must return boolean for error and a list of matrices objects
        #(the fields for which are detailed below)
        return error, matrices



############################################
#                                          #
#          schemas specifications          #
#                                          #
############################################

schemas = [
    {   'key': 'some_key',
        'examples': [1,2,3,4,5],
        'type': 'String' or 'Numeric',
        'suggestion': 'some_filter_name',
        #list of additional filter options based on type
        'options': ['some_filter', 'some_other_filter']
    },
    ...,
    {
        ...
    }
]


############################################
#                                          #
#        posted_data specifications        #
#                                          #
############################################

posted_data = {
    #matrixFilters is a dictionary where each key is a field of data
    #and the value is the object of specifications provided by the published filter
    "matrixFilters": {
        #example for text data using the TweetDocumentLEAN filter
        "text": {
            "classname":"TweetDocumentLEAN",
            "description":"Converts documents into a term-frequency matrix and associated documents.",
            "filter_id":"lean.python.TweetDocumentLEAN",
            "input":"String","name":"Twitter (LEAN)",
            "outputs":["documents.txt","dictionary.txt","matrix.mtx"],
            #parameters adjusted by the UI to include user inputs
            "parameters_spec":[ {"attrname":"include","name":"Include the following keywords","type":"input","value":""},
                                {"attrname":"exclude","name":"Exclude the following keywords","type":"input","value":""},
                                {"attrname":"lang","name":"Language","type":"input","value":""},
                                {"attrname":"limit","name":"Limit","type":"input","value":"5"},
                                {"attrname":"start","name":"Start time","type":"input","value":""},
                                {"attrname":"end","name":"End time","type":"input","value":""},
                                {"attrname":"geo","name":"Geo","type":"input","value":""}],
            "possible_names":["tweet"],
            "stage":"before",
            "type":"extract"}
        },
    #matrixFeatures is a list of fields selected by the user for inclusion in the generated matrix
    "matrixFeatures":["text"],
    #matrixFeaturesOriginal is the list of unaltered names selected by the user for inclusion in the generated matrix
    "matrixFeaturesOriginal":["text"],
    #matrixName is the user provided name for the generated matrix
    "matrixName":"test",
    #sourceName is the specific name of the portion of the original data to be used in the generated matrix
    "sourceName":"ows",
    #matrixTypes is a list of basic types for each of the selected fields for inclusion in the generated matrix
    "matrixTypes":["String"]
}


############################################
#                                          #
#            src specifications            #
#                                          #
############################################

src = {
    #datetime for point of creation
    "created": "2015-02-23 22:34:22.060675",
    #ip address for location of source files
    "host": "127.0.1.1",
    #ingest module that was used to ingest the source and will be used for matrix generation
    "ingest_id": "Spreadsheet",
    #list of matrices that have been created using this source (specificaiton follows below)
    "matrices": [],
    #user-provided name for the source
    "name": "iris",
    #absolute path for the location of the source files on the host
    "rootdir": "/var/www/analytics-framework/dataloader/data/caa1a3105a22477f8f9b4a3124cd41b6/",
    #unique id for location of the source
    "src_id": "caa1a3105a22477f8f9b4a3124cd41b6",
    #indication of the type of source: {file, conf, zip}
    "src_type": "file"
}



############################################
#                                          #
#         matrices specifications          #
#                                          #
############################################

matrices = [
    {
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
]
