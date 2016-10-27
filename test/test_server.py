#!/usr/bin/env python3
"""
test.py: the main tests for bedrock.
"""

from pprint import pprint
import requests
from src.client.client import BedrockAPI
from testhelp import expects

VAGRANTSERVER = "http://192.168.33.102:81/"
SERVER = "http://localhost:81/"
PRODSERVER = "http://bisiprod003:81/"
VERSION = "0.1"

if __name__ == "__main__":
    print("Running tests as main against server:%s as main" % SERVER)
    import argparse
    PARSER = argparse.ArgumentParser(
        description='test runner for bedrock-core, run from the client machine')
    PARSER.add_argument('--port', '-p', type=int, help='the port number for bedrock api default:81')
    ARGS = PARSER.parse_args()
    if ARGS.port:
        SERVER = "http://localhost:%d/" % ARGS.port

# def api(category, version, subcategory):
#     API = "%s/api/%s/%s/"
#     return API % (category, version, subcategory)


def log_failure(api, msg, response, expected_code, *args, **kwargs):
    """assert that a request has the expected code and log the message"""
    assert response.status_code == expected_code, "FAIL:%s:%d:%s:%s:%s:%s" % (
        msg, response.status_code, response.text, api.server, args, kwargs)


def unpack_singleton_list(possible_list):
    """if a length one list return the single item"""
    if isinstance(possible_list, list) and len(possible_list) == 1:
        return possible_list[0]
    else:
        print("Warn: input is not a length one list!")
        return possible_list


def validate_plot(plot):
    """check that a dict contains a javascript plot"""
    assert plot["data"][0:8] == '<script>', "FAIL: Plot is not a script!"
    assert plot["id"][0:3] == "vis", "FAIL: Plot does not have a vis_* id"
    assert "title" in plot, "FAIL: Plot does not have a title"
    assert "type" in plot, "FAIL: Plot does not have a type"
    return True


def check_api_list(api, category, subcategory):
    """check that we can request the list of endpoints available in a category/subcategory"""
    resp = api.list(category, subcategory)
    assert resp.status_code == 200, "Failed to get list of %s" % subcategory
    js_list = resp.json()
    print(js_list[0])
    assert len(js_list) > 0, "Failed to download any %s" % subcategory


def check_spreadsheet(api):
    """check that we can upload a spreadsheet"""
    sresp = api.ingest("Spreadsheet/")
    assert sresp.status_code == 200, "Failed to load Spreadsheet"
    spreadsheet = sresp.json()
    print(spreadsheet)
    assert spreadsheet["parameters"][0][
        "value"] == ".csv,.xls,.xlsx", "Spreadsheet opal cannot read appropriate filetpes"
    return sresp


def check_pca(api):
    """check that the api tells us PCA is available"""
    resp = api.analytic("Pca")
    endpoint = api.endpoint("analytics", "analytics/dimred")
    dimreds = requests.get(endpoint).json()
    assert 'Pca' in (d['analytic_id'] for d in dimreds), "Failed to find Pca in dimreds list"
    pprint(resp.json())
    assert resp.status_code == 200, "Failure: Pca is not installed on the server."
    return resp


def check_put(api, ssname, filename, ingest_id, group_id):
    """check that we can upload a source to the dataloader"""
    resp = api.put_source(ssname, ingest_id, group_id, {'file': open(filename, "rb")})
    pprint(resp.headers)
    created = resp.json()
    pprint(created)
    src_id = created['src_id']

    fetched = requests.get(api.endpoint("dataloader", "sources/%s" % src_id)).json()
    assert fetched['name'] == ssname, "failed to retrieve ingested data"
    return created, fetched


@expects(204, "Failed to Delete")
def check_delete_source(api, src_id):
    """deletes a source by its id and checks the return code."""
    url = api.endpoint("dataloader", "sources/%s" % src_id)
    resp = requests.delete(url)
    print(resp.text)
    return resp

def check_put_delete(api, ssname, filename, ingest_id, group_id):
    ''' Check to make sure it can put a file then delete that same file '''

    created, fetched = check_put(api, ssname, filename, ingest_id, group_id)
    pprint(created)
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

def check_make_matrix(api, source_id, matbody):
    """check that matrices can be made from a source"""
    # echo $matbody |  http post http://192.168.33.102:81/dataloader/api/0.1/sources/$src_id/
    # postdata = json.loads(matbody)
    resp = api.post("dataloader", "sources/%s/" % source_id, json=matbody)
    assert resp.status_code == 201, "Failed to create matrix: %d: %s" % (resp.status_code,
                                                                         resp.text)
    return resp.json()


def check_analysis(api, analytic_id, source_id, postdata):
    """check that we can make an analytic based on a source"""
    print("INFO: creating analytic at analytics/%s/" % source_id)
    resp = api.post("analytics", "analytics/%s/" % analytic_id, json=postdata)
    assert resp.status_code == 201, "Failed to run the analytic: %d: %s: %s" % (
        resp.status_code, resp.text, analytic_id)
    return resp.json()


def test_api_lists():
    bedrockapi = BedrockAPI(SERVER, VERSION)
    check_api_list(bedrockapi, "analytics", "analytics")
    check_api_list(bedrockapi, "analytics", "analytics/clustering")
    check_api_list(bedrockapi, "dataloader", "ingest")
    check_api_list(bedrockapi, "dataloader", "filters")
    spreadsheet = check_spreadsheet(bedrockapi)
    check_api_list(bedrockapi, "visualization", "visualization")

    ANALYTICS_API_TEST = "analytics/api/0.1/analytics/"
    ANALYTICS_API = bedrockapi.path("analytics", "analytics")
    assert ANALYTICS_API == ANALYTICS_API_TEST, \
           "generating api URLs is broken " + ANALYTICS_API + " " + ANALYTICS_API_TEST

    print("Available Analytics:")
    ans = bedrockapi.list("analytics", "analytics")
    pca = check_pca(bedrockapi)


def test_workflow_iris_pca():
    """test that we can upload the IRIS dataset as a csv and run PCA then make a plot."""
    print("Running tests against server:%s" % SERVER)
    bedrockapi = BedrockAPI(SERVER, VERSION)

    source_name = 'iris'
    group_id = 'default'

    created = {}
    fetched = {}
    available_sources = bedrockapi.list("dataloader", "sources/").json()
    source_id = ""

    if len(available_sources) < 4:
        created, fetched = check_put(bedrockapi, source_name, "./iris.csv", "Spreadsheet", group_id)
        source_id = created['src_id']
        print("INFO: created source: %s" % source_id)
    else:
        source_id = available_sources[0]['src_id']
        print("Available Sources are: %s" % (s['src_id'] for s in available_sources))
        print("Not uploading new source")
        fetched = requests.get(bedrockapi.endpoint("dataloader", "sources/%s/" % source_id)).json()

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
                'classname': 'TruthLabelsNumeric',
                'description': 'Extracts the truth labels.',
                'filter_id': 'TruthLabelsNumeric',
                'input': 'Numeric',
                'name': 'TruthLabels',
                'ouptuts': ['truth_labels.csv'],
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

    analytic_id = "Pca"
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

    plotname = "ClusterScatterTruth"
    resp = bedrockapi.post("visualization", "visualization/%s/" % plotname, json=getplot_data)
    log_failure(bedrockapi, "creating visualization %s" % plotname, resp, 200)
    plot = resp.json()
    validate_plot(plot)
    print("INFO: Tests PASS!")


def test_matrix():
    bedrockapi = BedrockAPI(SERVER, VERSION)
    exploredresp = bedrockapi.get('dataloader', 'sources/explorable')
    check_api_list(bedrockapi, "dataloader", "sources")
    assert exploredresp.status_code == 200
    explored = exploredresp.json()
    print(explored)
    mat = explored[0]
    src_id = mat['src_id']
    mat_id = mat['id']
    rootpath = mat['rootdir']
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


def test_deletions():
    bedrockapi = BedrockAPI(SERVER, VERSION)
    available_sources = bedrockapi.list("dataloader", "sources/").json()
    source = available_sources[0]
    source_id = source['src_id']
    fetched = requests.get(bedrockapi.endpoint("dataloader", "sources/%s/" % source_id)).json()
    source_name = 'iris-to-delete'
    group_id = 'default'
    created, fetched = check_put_delete(bedrockapi, source_name, "./iris.csv", "Spreadsheet", group_id)
