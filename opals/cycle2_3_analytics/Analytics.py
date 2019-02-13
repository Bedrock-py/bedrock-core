import pathlib
from bedrock.analytics.utils import Algorithm
import logging
from rpy2.robjects import r, pandas2ri
from rpy2.robjects.packages import importr


class Wrangle(Algorithm):

    def __init__(self):
        super(Wrangle, self).__init__()
        self.parameters = []
        self.inputs = []
        self.outputs = []
        self.name = 'Cycle2 Wrangle'
        self.type = 'GLM'
        self.description = 'Performs Stan GLM for NGS2 Cycle 2.'
        self.parameters_spec = [
            {"name": "Regression Formula", "attrname": "formula", "value": "", "type": "input"},
            {"name": "GLM family", "attrname": "family", "value": "binomial", "type": "input"}
        ]

    def check_parameters(self):
        return True

    def __build_df__(self, filepath):
        pass
        # featuresPath = filepath['features.txt']['rootdir'] + 'features.txt'
        # matrixPath = filepath['matrix.csv']['rootdir'] + 'matrix.csv'
        # df = pd.read_csv(matrixPath, header=-1)
        # featuresList = pd.read_csv(featuresPath, header=-1)

        #df.columns = featuresList.T.values[0]

        # return df

    def custom(self, **kwargs):
        # df = self.__build_df__(filepath)

        from rpy2.robjects.packages import importr
        base = importr('base')
        # do things that generate R warnings
        base.warnings()

        pandas2ri.activate()

        r("setwd('{}')".format(kwargs["filepath"] + ""))
        r("load('.RData')")

        # save R workspace and load workspaces between opals!
        # 1. load workspace created during data load

        rstan = importr("rstanarm")
        # rdf = pandas2ri.py2ri(df)
        # robjects.globalenv["rdf"] = rdf

        opal_dir = pathlib.Path(__file__).parent

        # Note: BoomTown Metadata needs to be present too or it will fail without real error
        r("source('{}/wrangle.R')".format(opal_dir))  # Load Wrangle

        r("save.image()")  # saves to .RData by default

        # rglmString = 'output <- stan_glmer({}, data = {}, family="{}")'.format(self.formula, "rdf", self.family)
        # logging.error(rglmString)
        # r(rglmString)
        # summary_txt = r('s<-summary(output)')
        # coef_table = r('data.frame(s$coefficients)')
        # self.results = {'matrix.csv': list(csv.reader(coef_table.to_csv().split('\n'))), 'summary.txt': [str(summary_txt)]}
