import csv
import os
import pathlib
import traceback

from bedrock.analytics.CONSTANTS import RESULTS_PATH
from bedrock.analytics.api import results_collection
from bedrock.analytics.utils import Algorithm, getCurrentTime, getNewId
import logging
from rpy2.robjects import r, pandas2ri
from rpy2.robjects.packages import importr


class ActiveLearning(Algorithm):

    def __init__(self):
        super(ActiveLearning, self).__init__()
        self.parameters = []
        self.inputs = []
        self.outputs = ['matrix.csv', 'summary.txt']
        self.name = 'Cycle 2 Active Learning'
        self.type = 'mcmc'
        self.description = 'Performs Active Learning'
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

        # Load these libraries - if not already loaded needed
        r('if (!require("pacman")) install.packages("pacman")')
        r('library ("pacman")')
        r("pacman::p_load(rstan, rstanarm, ggplot2, Hmisc, httr, bridgesampling, DT, dplyr, bayesplot, knitr)")
        r("set.seed(12345)")
        r("nIter = 10000")
        r("LOCAL <- TRUE")

        # save R workspace and load workspaces between opals!
        # 1. load workspace created during data load

        opal_dir = pathlib.Path(__file__).parent

        # 2. Run R Script
        r("source('{}/active_learning.R')".format(opal_dir))  # Active Learning

        r("save.image()")  # saves to .RData by default

        ranking_result = r("x.ranked.post.entropy")
        self.results = {'matrix.csv': list(csv.reader(ranking_result.to_csv().split('\n')))}

        self.write_results(kwargs['filepath'] + "output") # should it be results? + calling this since it's custom

        # store results in database

        try:
            # store metadata
            _, res_col = results_collection()

            try:
                src = res_col.find({'src_id': kwargs["src_id"]})[0]
            except IndexError:
                src = {}
                src['rootdir'] = os.path.join(RESULTS_PATH, kwargs["src_id"]) + '/output/'
                src['src'] = {}
                src['src_id'] = kwargs["src_id"]
                src['results'] = []
                res_col.insert(src)
                src = res_col.find({'src_id': kwargs["src_id"]})[0]

            res_id = getNewId()
            res = {}
            res['id'] = res_id
            res['rootdir'] = kwargs['filepath'] + "/output"
            res['name'] = self.name  # Name parameter
            res['src_id'] = kwargs["src_id"]
            res['created'] = getCurrentTime()
            res['analytic_id'] = kwargs["analytic_id"]
            res['parameters'] = kwargs["param1"]
            res['outputs'] = self.get_outputs()

            results = []
            for each in src['results']:
                results.append(each)
            results.append(res)
            res_col.update({
                'src_id': kwargs["src_id"]
            }, {'$set': {
                'results': results
            }})

            return res, 201

        except Exception as e:
            print(e)
            tb = traceback.format_exc()
            logging.error(tb)
            return tb, 406