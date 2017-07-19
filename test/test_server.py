#!/usr/bin/env python3
"""
test.py: the main tests for bedrock.
"""

#from future_builtins import filter

import logging
import sys
from pprint import pprint
import requests
import numpy as np
import pandas as pd
import pytest
from bedrock.client.client import BedrockAPI
sys.path.insert(0, 'test') #NOTE: run from bedrock-core / main folder
from testhelp import expects, is_numeric, column_types

VAGRANTSERVER = "http://192.168.33.102:81/"
SERVER = "http://localhost:81/"
PRODSERVER = "http://bisi3:9999/"

if __name__ == "__main__":
    print("Running tests as main against server:%s as main" % SERVER)
    import argparse
    PARSER = argparse.ArgumentParser(
        description='test runner for bedrock-core, run from the client machine')
    PARSER.add_argument('--port', '-p', type=int, help='the port number for bedrock api default:81')
    ARGS = PARSER.parse_args()
    if ARGS.port:
        SERVER = "http://localhost:%d/" % ARGS.port

# def api(category, subcategory):
#     API = "%s/%s/"
#     return API % (category, subcategory)


def log_failure(api, msg, response, expected_code, *args, **kwargs):
    """assert that a request has the expected code and log the message"""
    assert response.status_code == expected_code, "FAIL:%s:%d:%s:%s:%s:%s" % (
        msg, response.status_code, response.text, api.server, args, kwargs)


def unpack_singleton_list(possible_list):
    """if a length one list return the single item"""
    if isinstance(possible_list, list) and len(possible_list) == 1:
        return possible_list[0]
    else:
        print("Warn: input is not a length one list!") #why is this a problem?
        return possible_list


def validate_plot(plot):
    """check that a dict contains a javascript plot"""
    assert plot["data"][0:8] == '<script>', "FAIL: Plot is not a script!"
    assert plot["id"][0:3] == "vis", "FAIL: Plot does not have a vis_* id"
    assert "title" in plot, "FAIL: Plot does not have a title"
    #**why does title not equal the plotname parameter?
    assert "type" in plot, "FAIL: Plot does not have a type"
    return True


def check_api_list(api, category, subcategory):
    """check that we can request the list of endpoints available in a category/subcategory"""
    resp = api.list(category, subcategory)
    logging.info('Checking: \n\t%s', resp.url)
    assert resp.status_code == 200, "Failed to get list of %s" % subcategory
    js_list = resp.json()
    assert len(js_list) > 0, "Failed to download any %s" % subcategory
    logging.info("First entry:\n%s", pprint(js_list[0]))
    logging.info("Total number of entries for %s-%s: %s\n", category, subcategory, len(js_list))
    # classnames_str = ', '.join([d['classname'] for d in js_list])
    # print("List of classnames: {}\n".format(classnames_str))


def check_spreadsheet(api):
    """check that we can upload a spreadsheet"""
    '''
    Source code for ingest spreadsheet:
        https://github.gatech.edu/Bedrock/opal-dataloader-ingest-spreadsheet/blob/master/Spreadsheet.py
    '''
    sresp = api.ingest("opals.spreadsheet.Spreadsheet.Spreadsheet")
    print('Checking: ', sresp.url)
    assert sresp.status_code == 200, "Failed to load Spreadsheet"
    spreadsheet = sresp.json()
    pprint(spreadsheet)
    print('\n')
    assert spreadsheet["description"] == "Loads data from CSV or Microsft Excel spreadsheets.", "Spreadsheet description different than expected"
    assert spreadsheet["parameters"][0]["value"] == ".csv,.xls,.xlsx", "Spreadsheet opal cannot read appropriate filetypes"
    return sresp


def print_available_analytic_opals(api, category, subcategory):
    ''' Print list of available opals for a given analytic API category'''
    subcategory_pretty = ' '.join([w.capitalize() for w in subcategory.split('/')])
    print("Available {} Algorithms:".format(subcategory_pretty))
    ans = api.list(category, subcategory)
    available_analytic_opals = [d['analytic_id'] for d in ans.json()]
    if ans.json():
        try:
            print('\t', ', '.join(available_analytic_opals))
        except KeyError:
            print('\tNone')
    else:
        print('\tNone')
    print('\n')

    return available_analytic_opals


def print_all_available_analytic_opals(api):
    ''' Print list of all available analytic opals'''
    #PRINT AVAILABLE ANALYTIC METHODS
    category_subcategory_list = [('analytics', 'analytics'),
                                 ('analytics', 'analytics/clustering'),
                                 ('analytics', 'analytics/classification'),
                                 ('analytics', 'analytics/dimred'),
                                 ('analytics', 'analytics/models')]
    for c_sc in category_subcategory_list:
        _ = print_available_analytic_opals(api, c_sc[0], c_sc[1])


def check_analytic_opal_availability(api, category, subcategory, opal_name):
    """check that the api opal_name exists in given location"""
    # TODO: this only works on analytics, but could be extended to all categories.
    resp = api.analytic(opal_name)
    pprint(resp.json())
    assert resp.status_code == 200, "Failure: {} is not installed on the server.".format(opal_name)

    endpoint = api.endpoint(category, subcategory)
    content = requests.get(endpoint).json()
    opallist = (d['analytic_id'] for d in content)
    assert opal_name in opallist, "Failed to find {} in {} list".format(opal_name, subcategory)
    print('\n')
    return resp


def check_existing_opals(api):
    ''' list all available and check individual opals '''
    print_all_available_analytic_opals(api)

    #CHECK AVAILABILITY OF OPALS
    pca = check_analytic_opal_availability(api, 'analytics', 'analytics/dimred', 'opals.dimred.Pca.Pca')
    assert pca is not None
    kmeans = check_analytic_opal_availability(api, 'analytics', 'analytics/clustering', 'opals.clustering.Kmeans.Kmeans')
    assert kmeans is not None

def check_put(api, ssname, filename, ingest_id, group_id):
    """check that we can upload a source to the dataloader"""
    resp = api.put_source(ssname, ingest_id, group_id, {'file': open(filename, "rb")})
    pprint(resp.headers)
    pprint(resp.text)
    created = resp.json()
    pprint(created)
    src_id = created['src_id']

    fetched = requests.get(api.endpoint("dataloader", "sources/%s" % src_id)).json()
    #**WHY IS FETCHED['MATRICES'] == []? - JP: Because Matrices aren't created yet.  This is just a source for matrices
    assert fetched['name'] == ssname, "failed to retrieve ingested data"
    return created, fetched


@expects(204, "Failed to Delete")
def check_delete_source(api, src_id):
    """deletes a source by its id and checks the return code."""
    url = api.endpoint("dataloader", "sources/%s" % src_id)
    resp = requests.delete(url)
    print(resp.text)
    return resp

def check_put_deletef(api, ssname, filename, ingest_id, group_id):
    ''' Check to make sure it can put a file then delete that same file '''

    created, fetched = check_put(api, ssname, filename, ingest_id, group_id)
    src_id = created['src_id']
    print('Put src_id: {}'.format(src_id))
    check_delete_source(api, src_id)
    fetch = requests.get(api.endpoint("dataloader", "sources/%s" % src_id))
    print(fetch.json())
    print(fetch.text)
    assert fetch.status_code != 200, "Source was not deleted."
    return created, fetched

    # TODO one day deletions will tell you what they deleted so that you could check this.
    # assert resp['src_id'] == created['src_id'], "Could not delete %s"%src_id


def check_explore_results(
        api=None,
        source_id='',
        ref_df_filepath=''):
    ''' Compare exploration results (descriptive statistice) to those of an identical dataframe '''

    #GET DESCRIPTIVE STATISTICS FROM DATALOADER EXPLORE API
    endpoint = api.endpoint("dataloader", "sources/%s/explore" % source_id)
    print("INFO: Getting source: %s" % endpoint)
    resp = requests.get(endpoint)
    assert resp.status_code == 200, \
        "Response code: {}, Reason: {}".format(resp.status_code, resp.reason)

    #DEFINE RECEIVED DATA TO COMPARE AGAINST
    exploration_results = resp.json()
    mat_name = list(exploration_results.keys())[0]
    exploration_results = exploration_results[mat_name]['fields']

    #IMPORT REFERENCE DF
    ref_df = pd.read_csv(ref_df_filepath)
    describe_df = ref_df.describe()
    desc_stat_checklist = [idx for idx in describe_df.index.tolist() if idx != 'count']

    #DETERMINE NUMERIC AND CATEGORICAL COLUMN NAMES
    numeric_keys = set(['std', 'min', 'max', '50%', 'suggestions', '25%', '75%', 'type', 'mean'])
    is_numeric_column = lambda v: set(v.keys()) == numeric_keys
    numeric_columns = [f for f, v in exploration_results if is_numeric_column(v)]
    categorical_columns = []

    non_numeric = list(set(exploration_results.keys()).difference(numeric_columns))
    for field in non_numeric:
        categorical_vals = set(ref_df[field].unique().tolist()+['suggestions', 'type'])
        if set(exploration_results[field].keys()) == categorical_vals:
            categorical_columns.append(field)

    #CHECK NUMERIC COLUMNS
    for field in numeric_columns:
        for chk in desc_stat_checklist:
            try:
                ref_chk = round(describe_df[field][chk], 1)
                resp_chk = round(exploration_results[field][chk], 1)
                assert ref_chk == resp_chk, "Exploration results do not match locally-hosted reference dataframe:\n\t{} != {}\t{} ref != {} response".format(ref_chk, resp_chk, chk, chk)
            except KeyError:
                logging.info("Numeric field match for %s and check %s not found in reference dataframe.", field, chk)
    logging.info('All numeric exploration results matched pandas .describe() function in reference dataframe (rounded to one decimal place)')
    logging.info('Fields checked: %s\n', numeric_columns)

    #CHECK CATEGORICAL COLUMNS
    for field in categorical_columns:
        val_counts_ref = ref_df[field].value_counts()
        val_counts_resp = exploration_results[field]
        for k in val_counts_resp.keys():
            if k in val_counts_ref.index.tolist():
                assert val_counts_ref[k] == val_counts_resp[k],\
                       'Ref dataset does not match response for {}, {}'.format(field, k)
    logging.info("All exploration categorical value counts matched reference dataframe.")
    logging.info("Fields checked: %s\n", categorical_columns)

    return resp


def check_make_matrix(api, source_id, matbody):
    """check that matrices can be made from a source"""
    # echo $matbody |  http post http://192.168.33.102:81/dataloader/sources/$src_id/
    # postdata = json.loads(matbody)
    resp = api.post("dataloader", "sources/%s/" % source_id, json=matbody)
    # assert resp.status_code == 201, "Failed to create matrix: %d: %s" % (resp.status_code,
    #                                                                      resp.text)
    output = resp.json()
    logging.info('tried to make matrix %s. Response:\n%s', source_id, output)
    return output


def check_analysis(api, analytic_id, source_id, postdata):
    """Check that we post parameters to run an analytic based on a source"""
    '''
    Parameters:
        api = BedrockAPI from src/client/client
        analytic_id - 'Pca'
        source_id - '010d48dbe28e4a3ca7ee8573df542745'
        postdata description in workflow_2

    Returns a json of the post analytics analytics/analytic_id response

    Throws an error when the analytic doesn't run properly on the server
    '''
    print("INFO: creating analytic at analytics/%s/" % source_id)
    resp = api.post("analytics", "analytics/%s" % analytic_id, json=postdata)
    assert resp.status_code == 201, "Failed to run the analytic: %d: %s: %s" % (
        resp.status_code, resp.text, analytic_id)
    return resp.json()


def test_api_lists():
    ''' checks available api's '''
    bedrockapi = BedrockAPI(SERVER)
    check_api_list(bedrockapi, "analytics", "analytics")
    check_api_list(bedrockapi, "analytics", "analytics/clustering")
    check_api_list(bedrockapi, "dataloader", "ingest")
    check_api_list(bedrockapi, "dataloader", "filters")
    check_api_list(bedrockapi, "visualization", "visualization")
    spreadsheet = check_spreadsheet(bedrockapi)
    assert spreadsheet is not None
    check_api_list(bedrockapi, "visualization", "visualization")

    analytics_api_test = "analytics/analytics/"
    analytics_api = bedrockapi.path("analytics", "analytics")
    assert analytics_api == analytics_api_test, \
           "generating api URLs is broken " + analytics_api + " " + analytics_api_test

    print("Available Analytics:")
    ans = bedrockapi.list("analytics", "analytics")
    pca = check_analytic_opal_availability(bedrockapi, 'analytics', 'analytics/dimred', 'opals.dimred.Pca.Pca')
    assert ans is not None
    assert pca is not None

def test_workflow_iris_pca():
    """test that we can upload the IRIS dataset as a csv and run PCA then make a plot."""
    print("Running tests against server:%s" % SERVER)
    bedrockapi = BedrockAPI(SERVER)

    source_name = 'iris'
    group_id = 'default'

    created = {}
    fetched = {}
    available_sources = bedrockapi.list("dataloader", "sources/").json()
    source_id = ""


    created, fetched = check_put(bedrockapi, source_name, "./iris.csv", "opals.spreadsheet.Spreadsheet.Spreadsheet", group_id)
    source_id = created['src_id']
    if (created['error'] == 1):
        print("INFO: source already existed: %s" % source_id)
    else:
        print("INFO: created source: %s" % source_id)

    endpoint = bedrockapi.endpoint("dataloader", "sources/%s/explore/" % source_id)
    print("INFO: Getting source: %s" % endpoint)
    resp = requests.get(endpoint)
    matrix_id = 'iris_mtx'
    matrix_name = 'iris_mtx'

    feature_name_list = ['petal_length', 'petal_width', 'sepal_length', 'sepal_width', 'species']
    feature_name_list_original = [
        'petal_length', 'petal_width', 'sepal_length', 'sepal_width', 'species'
    ]
    column_types = ['Numeric', 'Numeric', 'Numeric', 'Numeric', 'String']
    matbody = {
        'matrixFeatures': feature_name_list,
        'matrixFeaturesOriginal': feature_name_list_original,
        'matrixFilters': {
            'petal_length': {},
            'petal_width': {},
            'sepal_length': {},
            'sepal_width': {},
            'species': {
                'classname': 'opals.truth.TruthLabelsNumeric.TruthLabelsNumeric',
                'description': 'Extracts the truth labels.',
                'filter_id': 'opals.truth.TruthLabelsNumeric.TruthLabelsNumeric',
                'input': 'Numeric',
                'name': 'TruthLabels',
                'outputs': ['truth_labels.csv'],
                'parameters': [],
                'possible_names': ['class', 'truth'],
                'stage': 'after',
                'type': 'extract'
            }
        },
        'matrixName': matrix_name,
        'matrixTypes': column_types,
        'sourceName': source_name
    }

    url = bedrockapi.endpoint("dataloader", "sources/%s" % (source_id))
    print("INFO: Posting matrix to:%s" % url)
    resp = requests.post(url, json=matbody)
    log_failure(bedrockapi, "posting matrix %s" % matbody, resp, 201)

    mtx_res = unpack_singleton_list(check_make_matrix(bedrockapi, source_id, matbody))
    print("INFO: received matrix post response")
    pprint(mtx_res)

    analytic_id = "opals.dimred.Pca.Pca"
    # to apply the analysis to the matrix
    print("INFO: creating analysis_postdata")
    analysis_postdata = {
        'inputs': {
            'features.txt': mtx_res,
            'matrix.csv': mtx_res
        },
        'name': 'iris-pca',
        'parameters': [{
            'attrname': 'numDim',
            'max': 15,
            'min': 1,
            'name': 'Dimensions',
            'step': 1,
            'type': 'input',
            'value': 2
        }],
        'src': [mtx_res]    # this is a list because the server expects a list
    }
    analysis_res = check_analysis(bedrockapi, analytic_id, source_id, analysis_postdata)
    print("INFO: received analytic post response")
    analysis_res = unpack_singleton_list(analysis_res)

    print("INFO: print analysis response")
    pprint(analysis_res)

    viz_postdata = [mtx_res]
    resp = bedrockapi.post("visualization", "visualization/", json=viz_postdata)
    log_failure(bedrockapi, "listing visualizations", resp, 200)

    plot_params_list = [{
        'attrname': 'x_feature',
        'name': 'X feature index',
        'type': 'input',
        'value': 0
    }, {
        'attrname': 'y_feature',
        'name': 'Y feature index',
        'type': 'input',
        'value': 1
    }]
    getplot_data = {
        'inputs': {
            'matrix.csv': analysis_res,
            'truth_labels.csv': mtx_res
        },
        'parameters': plot_params_list
    }

    plotname = "opals.scatterplot.ClusterScatterTruth.ClusterScatterTruth"
    resp = bedrockapi.post("visualization", "visualization/%s/" % plotname, json=getplot_data)
    log_failure(bedrockapi, "creating visualization %s" % plotname, resp, 200)
    plot = resp.json()
    validate_plot(plot)
    print("INFO: Tests PASS!")


def test_matrix():
    bedrockapi = BedrockAPI(SERVER)
    exploredresp = bedrockapi.get('dataloader', 'sources/explorable')
    check_api_list(bedrockapi, "dataloader", "sources")
    assert exploredresp.status_code == 200
    explored = exploredresp.json()
    print(explored)
    mat = next(source for source in explored if source['name'] == 'iris')
    src_id = mat['src_id']
    mat_id = mat['matrices'][0]['id']
    rootpath = mat['matrices'][0]['rootdir']
    print('matrix root path: %s %s %s' % (src_id, mat_id, rootpath))
    sourceresp = bedrockapi.get('dataloader', 'sources/' + src_id)
    assert sourceresp.status_code == 200
    source = sourceresp.json()
    assert source['src_id'] == src_id
    # print('source')
    # print(source)

    outputresp = bedrockapi.get('dataloader', 'sources/%s/%s/output/' % (src_id, mat_id))
    output = outputresp.text
    print('output')
    print(output)
    # TODO this should be a 200 but the opals have to write there first
    # see issue #45 on github.gatech.edu/Bedrock/bedrock-core
    assert outputresp.status_code == 404
    assert len(output) > 0


def test_analytics():
    bedrockapi = BedrockAPI(SERVER)
    optdata = [{'outputs': 'matrix.csv'}]
    resp = bedrockapi.post('analytics', 'analytics/options', json=optdata)
    assert resp.status_code == 400

    optdata = [{'outputs': ['matrix.csv']}]
    resp = bedrockapi.post('analytics', 'analytics/options', json=optdata)
    print(resp.text)
    assert resp.status_code == 200
    opts = resp.json()
    assert len(opts) > 0

def test_deletions():
    bedrockapi = BedrockAPI(SERVER)
    available_sources = bedrockapi.list("dataloader", "sources/").json()
    source = available_sources[0]
    source_id = source['src_id']
    fetched = requests.get(bedrockapi.endpoint("dataloader", "sources/%s/" % source_id)).json()
    source_name = 'iris-to-delete'
    group_id = 'default'
    created, fetched = check_put_deletef(bedrockapi, source_name, "./iris.csv", "opals.spreadsheet.Spreadsheet.Spreadsheet", group_id)


def validate_api_paths(api):
    ''' validates various bedrockapi.path responses '''
    #CHECK BEDROCKAPI.PATH
    ANALYTICS_API_TEST = "analytics/analytics/"
    ANALYTICS_API = api.path("analytics", "analytics")
    assert ANALYTICS_API == ANALYTICS_API_TEST, \
           "generating api URLs is broken " + ANALYTICS_API + " " + ANALYTICS_API_TEST

    DATALOADER_FILTERS_API_TEST = "dataloader/filters/"
    DATALOADER_FILTERS_API = api.path("dataloader", "filters")
    assert DATALOADER_FILTERS_API == DATALOADER_FILTERS_API_TEST, \
           "generating api URLs is broken " + DATALOADER_FILTERS_API + " " + DATALOADER_FILTERS_API_TEST

    VISUALIZATION_API_TEST = "visualization/visualization/"
    VISUALIZATION_API = api.path("visualization", "visualization")
    assert VISUALIZATION_API == VISUALIZATION_API_TEST, \
           "generating api URLs is broken " + VISUALIZATION_API + " " + VISUALIZATION_API_TEST


def put_and_or_get_dataset(api,
                           source_name,
                           group_id,
                           filepath_to_put,
                           source_id_of_dataset_to_get=None):
    ''' puts dataset, gets specific dataset, or gets first datset in list and returns source_id'''
    '''
    if not putting, filepath_to_put=''
    if not getting, source_id_of_dataset_to_get=''
    same naming conventions/descriptions for these variables as in workflow_2
    '''

    #GET AND/OR PUT DATASET
    created = {}
    fetched = {}
    available_sources = api.list("dataloader", "sources").json()
    source_id = ""

    if filepath_to_put:
        created, fetched = check_put(api, source_name, filepath_to_put,
                                     "opals.spreadsheet.Spreadsheet.Spreadsheet", group_id)

        source_id = created['src_id']
        logging.info("created source: %s", source_id)

    elif source_id_of_dataset_to_get:
        source_id = source_id_of_dataset_to_get
        assert len([r for r in available_sources if r['src_id'] == source_id]), \
            "source_id may not exist on server"
        matching_source = [r for r in available_sources if r['src_id'] == source_id][0]
        logging.info("Not uploading new source. using user-defined source: %s at %s.",
                     matching_source['name'], matching_source['rootdir'])
        fetched = requests.get(
            api.endpoint("dataloader", "sources/%s/" % source_id)).json()
    else:
        logging.debug("Available Source IDs are: \n%s",
                      ', '.join([s['src_id'] for s in available_sources]))
        source_id = available_sources[0]['src_id']

        logging.info("Not uploading new source. using first available source: \
                %s at %s.", available_sources[0]['name'], available_sources[0]['rootdir'] )
        fetched = requests.get(api.endpoint("dataloader", "sources/%s/" % source_id)).json()
    print('\n')

    return source_id, fetched


def automate_matrix_def_from_ref_df(
        source_name='',
        ref_df_filepath='',
        truth_labels='',
        label_filters_dict= {'classname': 'opals.truth.TruthLabelsNumeric.TruthLabelsNumeric',
                             'description': 'Extracts the truth labels.',
                             'filter_id': 'opals.truth.TruthLabelsNumeric.TruthLabelsNumeric',
                             'input': 'Numeric',
                             'name': 'TruthLabels',
                             'outputs': ['truth_labels.csv'],
                             'parameters': [],
                             'possible_names': ['class', 'truth'],
                             'stage': 'after',
                             'type': 'extract'
            }
    ):
    #TO DO: UPDATE THIS TO ALLOW CUSTOM FILTERING FOR EACH COLUMN - NOT JUST THE TRUTH LABELS
    ''' create matrix definition via reference dataframe to post to BedrockAPI'''
    '''
    EXAMPLE USAGE:
    source_name='iris'
    ref_df_filepath="test/test_datasets/iris.csv"
    truth_labels='species',
    label_filters_dict= {'classname': 'TruthLabelsNumeric',
                'description': 'Extracts the truth labels.',
                'filter_id': 'TruthLabelsNumeric',
                'input': 'Numeric',
                'name': 'TruthLabels',
                'outputs': ['truth_labels.csv'],
                'parameters': [],
                'possible_names': ['class', 'truth'],
                'stage': 'after',
                'type': 'extract'
            } #CAN BE UPDATED IN ACCORDANCE WITH THE API
    '''
    #AUTOMATE TO MATRIX DEFINITION
    matrix_name = source_name+'_mtx'

    ref_df = pd.read_csv(ref_df_filepath)
    feature_name_list = [str(c) for c in ref_df.columns]
    feature_name_list_original = feature_name_list

    #DEFINE matrixTypes / column types
    columntypes = column_types(ref_df)
    matfilters = dict((col, label_filters_dict if col == truth_labels else {})
                      for col in feature_name_list)
    matfilters[truth_labels] = label_filters_dict
    matbody = dict(matrixFeatures=feature_name_list,
                   matrixFeaturesOriginal=feature_name_list_original,
                   matrixFilters=matfilters,
                   matrixName=matrix_name,
                   matrixTypes=columntypes,
                   sourceName=source_name)

    return matbody


def get_available_viz_list(api, mtx_res):
    '''RETURN A LIST OF APPLICABLE VISUALIZATIONS FOR YOUR GIVEN ANALYTIC_ID'''
    '''
    api = BedrockAPI
    mtx_res lists the identifying characteristics of the matrix you're using on the server
        for more detail about its creation and usage, see the learnings doc
    '''
    viz_postdata = [mtx_res]
    resp = api.post(
        "visualization", "visualization/", json=viz_postdata)
    log_failure(api, "listing visualizations", resp, 200)
    available_visualization_methods = [d['classname'] for d in resp.json()]
    print("Available visualization methods for your matrix (mtx_res) are:")
    print(available_visualization_methods)
    print('\n')

    return available_visualization_methods


def workflow_2(
        filepath_to_put='',
        source_id_of_dataset_to_get='',
        source_name='',
        group_id='default',
        truth_labels='',
        matbody={},
        analytic_id='',
        analysis_postdata={},
        check_plot=True,
        plot_params_list = [],
        plotname = ''
        ):
    """test that we can upload a dataset as a csv and run an analysis then make a plot."""
    '''
        optional - use one of the two:
            filepath_to_put='', #"test/test_datasets/iris.csv"
            source_id_of_dataset_to_get='', #'010d48dbe28e4a3ca7ee8573df542745'
        example usage:
            source_name='iris'
            group_id='default'
            truth_labels='species'
            matbody= see test_workflow_iris_pca matbody for example
            analytic_id='Pca'
            analysis_postdata={
                'inputs': {
                    'features.txt': None,
                    'matrix.csv': None
                },
                'name': 'iris-pca',
                'parameters': [{
                    'attrname': 'numDim',
                    'max': 15,
                    'min': 1,
                    'name': 'Dimensions',
                    'step': 1,
                    'type': 'input',
                    'value': 2
                }],
                'src': []    # this is a list because the server expects a list
            }
            check_plot=True/False
            plot_params_list=[{
                'attrname': 'x_feature',
                'name': 'X feature index',
                'type': 'input',
                'value': 0
            }, {
                'attrname': 'y_feature',
                'name': 'Y feature index',
                'type': 'input',
                'value': 1
            }]
            plotname="ClusterScatterTruth"

    currently only works with iris dataset - bball dataset not working
    '''
    print("Running tests against server: %s" % SERVER)
    print('\n')

    api = BedrockAPI(SERVER) #src/client/client.py

    spreadsheet = check_spreadsheet(api)

    validate_api_paths(api)

    source_id, fetched = put_and_or_get_dataset(api, source_name, group_id, filepath_to_put)

    #POST MATRIX DEFINITION AND FILTER(S) TO SOURCE ID
    mtx_res = check_make_matrix(api, source_id, matbody) #should return a len==1 list of params updated
    mtx_res = unpack_singleton_list(mtx_res)
    print("INFO: received matrix post response")
    pprint(mtx_res)
    print('\n')
    # For more info about mtx_res, see the learnings doc

    #UPDATE PARAMETERS TO POST TO ANALYTICS/ANALYTIC_ID TO RUN ANALYTIC OF CHOICE
    #NOTE: this may not generalize depending on the params expected from other analyses
    for k in analysis_postdata['inputs'].keys():
        analysis_postdata['inputs'][k] = mtx_res
    analysis_postdata['src'] = [mtx_res]
    print('The parameters sent to the post request are:')
    pprint(analysis_postdata)
    print('\n')
    #For more info about analysis_postdata, see the associated learnings doc

    # Apply the analytic_id to the matrix
    print("INFO: creating analysis_postdata")
    analysis_res = check_analysis(api, analytic_id,
                                  source_id, analysis_postdata)
    print("INFO: received analytic post response")
    analysis_res = unpack_singleton_list(analysis_res)
    print("INFO: print analysis response")
    pprint(analysis_res) #analysis_res documents identifying params of analysis that we just ran
    print('\n')

    available_vizs = get_available_viz_list(api, mtx_res)
    if plotname not in available_vizs:
        logging.warning('%s not listed in available visualization for your dataset', plotname)

    getplot_data = {
        'inputs': {},
        'parameters': plot_params_list
    }

    plot_inputs = getplot_data['inputs']
    if plotname == 'opals.scatterplot.ClusterScatterTruth.ClusterScatterTruth':
        plot_inputs['matrix.csv'] = analysis_res
        plot_inputs['truth_labels.csv'] = mtx_res
    if plotname == 'opals.scatterplot.ClusterScatter.ClusterScatter':
        plot_inputs['matrix.csv'] = mtx_res
        plot_inputs['assignments.csv'] = analysis_res
    if plotname == 'opals.scatterplot.Scatter.Scatter':
        plot_inputs['matrix.csv'] = analysis_res
        plot_inputs['features.txt'] = mtx_res

    resp = api.post(
        "visualization", "visualization/%s/" % plotname, json=getplot_data)
    log_failure(api, "creating visualization failed for %s" % plotname, resp, 200)
    plot = resp.json()
    validate_plot(plot)
    print('Successfully created plot for {} {} {}'.format(
                source_name, analytic_id, plotname))
    print('\n')

    # #NEEDS WORK - want to save so that you can instantly open it in a browser
    # viz_html = resp.json()['data']
    # with open("test/visualizations/viz_{}_{}_{}.html".format(source_name, analytic_id, plotname), "w") as text_file:
    #     text_file.write(viz_html)

    print("INFO: Tests PASS!")


# @pytest.mark.skip('still uses precalculated UUIDs')
def test_put_iris():
    bedrockapi = BedrockAPI(SERVER)
    check_put_deletef(bedrockapi, 'iris', "test/test_datasets/iris.csv",
                      "opals.spreadsheet.Spreadsheet.Spreadsheet", 'default')

    # check_explore_results(api=bedrockapi,
    #                       source_id='',
    #                       ref_df_filepath="test/test_datasets/iris.csv")

MATBODY = automate_matrix_def_from_ref_df(
    source_name='iris',
    ref_df_filepath="test/test_datasets/iris.csv",
    truth_labels='species',
    label_filters_dict= {'classname': 'opals.truth.TruthLabelsNumeric.TruthLabelsNumeric',
                'description': 'Extracts the truth labels.',
                'filter_id': 'opals.truth.TruthLabelsNumeric.TruthLabelsNumeric',
                'input': 'Numeric',
                'name': 'TruthLabels',
                'outputs': ['truth_labels.csv'],
                'parameters': [],
                'possible_names': ['class', 'truth'],
                'stage': 'after',
                'type': 'extract'
            }
    )

# IRIS-PCA-CLUSTERSCATTERTRUTH
# RUNS PROPERLY ON "http://bisi3:9999/"
# @pytest.mark.skip(reason="doesn't work need to update parameters")
def test_iris_pca_clusterscattertruth():
    workflow_2(
        filepath_to_put="test/test_datasets/iris.csv",
        source_id_of_dataset_to_get='',
        source_name='iris',
        group_id='default',
        truth_labels='species',
        matbody=MATBODY,
        analytic_id="opals.dimred.Pca.Pca",
        analysis_postdata={
            'inputs': {
                'features.txt': None,
                'matrix.csv': None
            },
            'name': 'iris-pca',
            'parameters': [{
                'attrname': 'numDim',
                'max': 15,
                'min': 1,
                'name': 'Dimensions',
                'step': 1,
                'type': 'input',
                'value': 2
            }],
            'src': []    # this is a list because the server expects a list
        },
        check_plot=True,
        plot_params_list=[{
            'attrname': 'x_feature',
            'name': 'X feature index',
            'type': 'input',
            'value': 0
        }, {
            'attrname': 'y_feature',
            'name': 'Y feature index',
            'type': 'input',
            'value': 1
        }],
        plotname="opals.scatterplot.ClusterScatterTruth.ClusterScatterTruth"
    )

#RUNS PROPERLY ON "http://bisi3:9999/"
# @pytest.mark.skip(reason="doesn't work need to update parameters")
def test_iris_Lda_clusterscattertruth():
    workflow_2(
        filepath_to_put='test/test_datasets/iris.csv',
        source_id_of_dataset_to_get='',
        source_name='iris',
        group_id='default',
        truth_labels='species',
        matbody=MATBODY,
        analytic_id="opals.dimred.Lda.Lda",
        analysis_postdata={
            'inputs': {
                'truth_labels.csv': None,
                'matrix.csv': None
            },
            'name': 'iris-lda',
            'parameters': [{
                "attrname": "numDim",
                "max": 15,
                "min": 1,
                "name": "Dimensions",
                "step": 1,
                "type": "input",
                "value": 2
              }],
            'src': []
        },
        check_plot=True,
        plot_params_list=[{
            'attrname': 'x_feature',
            'name': 'X feature index',
            'type': 'input',
            'value': 0
        }, {
            'attrname': 'y_feature',
            'name': 'Y feature index',
            'type': 'input',
            'value': 1
        }],
        plotname="opals.scatterplot.ClusterScatterTruth.ClusterScatterTruth"
    )

#RUNS PROPERLY ON "http://bisi3:9999/"
# @pytest.mark.skip(reason="doesn't work need to update parameters")
def test_iris_Lda_scatter():
    workflow_2(
        filepath_to_put='test/test_datasets/iris.csv',
        source_id_of_dataset_to_get='',
        source_name='iris',
        group_id='default',
        truth_labels='species',
        matbody=MATBODY,
        analytic_id="opals.dimred.Lda.Lda",
        analysis_postdata={
            'inputs': {
                'truth_labels.csv': None,
                'matrix.csv': None
            },
            'name': 'iris-lda',
            'parameters': [{
                "attrname": "numDim",
                "max": 15,
                "min": 1,
                "name": "Dimensions",
                "step": 1,
                "type": "input",
                "value": 2
              }],
            'src': []
        },
        check_plot=True,
        plot_params_list=[{
            'attrname': 'x_feature',
            'name': 'X feature index',
            'type': 'input',
            'value': 0
        }, {
            'attrname': 'y_feature',
            'name': 'Y feature index',
            'type': 'input',
            'value': 1
        }],
        plotname="opals.scatterplot.Scatter.Scatter"
    )

#RUNS PROPERLY ON "http://bisi3:9999/"
# @pytest.mark.skip(reason="doesn't work need to update parameters")
def test_iris_kmeans_clusterscatter():
    workflow_2(
        filepath_to_put="test/test_datasets/iris.csv",
        source_id_of_dataset_to_get='',
        source_name='iris',
        group_id='default',
        truth_labels='species',
        matbody=MATBODY,
        analytic_id='opals.clustering.Kmeans.Kmeans',
        analysis_postdata={
            "inputs": {
                "matrix.csv": None
            },
            "name": "iris-KMeans",
            "parameters": [
                {
                    "attrname": "numClusters",
                    "max": 15,
                    "min": 1,
                    "name": "Clusters",
                    "step": 1,
                    "type": "input",
                    "value": 3
                }
            ],
            "src": []
        },
        check_plot=True,
        plot_params_list=[{
            'attrname': 'x_feature',
            'name': 'X feature index',
            'type': 'input',
            'value': 0
        }, {
            'attrname': 'y_feature',
            'name': 'Y feature index',
            'type': 'input',
            'value': 1
        }],
        plotname="opals.scatterplot.ClusterScatter.ClusterScatter"
    )


#START HERE
@pytest.mark.skip(reason='need to update parameters')
def test_iris_centroid():
    workflow_2(
        filepath_to_put="test/test_datasets/iris.csv",
        source_name='iris',
        group_id='default',
        truth_labels='species',
        analytic_id='Centroid',
        analysis_postdata={
            "inputs": {
                "matrix.csv": None,
                "truth_labels.csv": None
            },
            "name": "Centroid",
            "parameters": [
                {
                    "attrname": "numDim",
                    "max": 15,
                    "min": 1,
                    "name": "Dimensions",
                    "step": 1,
                    "type": "input",
                    "value": 2
                }
            ],
            "src": []
        },
        check_plot=True,
        plot_params_list=[
            {
                "attrname": "x_feature",
                "name": "X feature index",
                "type": "input",
                "value": 0
            },
            {
                "attrname": "y_feature",
                "name": "Y feature index",
                "type": "input",
                "value": 1
            }
        ],
        plotname="opals.scatterplot.ClusterScatter.ClusterScatter",
    )

def make_bball_matrix():
    """load basketball data from a csv file."""
    #SAVE TO TXT
    url = 'https://raw.githubusercontent.com/chriseal/udacity_data_analyst/master/2_intro_to_data_science/data/baseball_stats.csv'
    resp = requests.get(url)
    import csv
    data = csv.reader(resp.text)
    filepath = 'test/test_datasets/bball.txt'
    with open(filepath, 'w') as outfile:
        outfile.write(resp.text)

    #CLEAN AND SAVE TO CSV
    data = pd.read_csv(filepath)
    data.dropna(axis=0, how='any', inplace=True)
    data = data.query("avg != 0.000").reset_index(drop=True).copy()
    data = data.query("height != ' '").reset_index(drop=True).copy()
    data = data.query("weight != ' '").copy()
    data = data.reset_index(drop=True).copy()
    data['height'] = data.height.astype(int)
    data['weight'] = data.height.astype(int)

    data.drop('name', axis=1, inplace=True)

    data.to_csv(filepath.split('.')[0]+'.csv', index=False)


#START HERE ON BBALL THEN WORK ON THE IF False: PORTION OF WORKFLOW_2
@pytest.mark.skip(reason="doesn't work need to update parameters")
def test_bball_kmeans():
    workflow_2(
        filepath_to_put='', #'test/test_datasets/bball.csv'
        source_id_of_dataset_to_get='0960083d8a374aacada4c2f2be59d72f',
        source_name='bball',
        group_id='default',
        analytic_id='opals.clustering.Kmeans.Kmeans',
        analysis_postdata={
            "inputs": {
                "matrix.csv": None
            },
            "name": "bball-KMeans",
            "parameters": [
                {
                    "attrname": "numClusters",
                    "max": 15,
                    "min": 1,
                    "name": "Clusters",
                    "step": 1,
                    "type": "input",
                    "value": 3
                }
            ],
            "src": []
        },
        check_plot=False
    )
