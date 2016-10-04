#!/usr/bin/env python3
"""
test.py: the main tests for bedrock.
"""

import requests
from pprint import pprint
import subprocess
import json

VAGRANTSERVER = "http://192.168.33.102:81/"
SERVER = "http://localhost:81/"
PRODSERVER = "http://bisiprod003:81/"
VERSION = "0.1"

if __name__ == "__main__":
    print("Running tests as main against server:%s" % SERVER)
    import argparse
    parser = argparse.ArgumentParser(description='test runner for bedrock-core, run from the client machine')
    parser.add_argument('--port', '-p', type=int, help='the port number for bedrock api default:81')
    args = parser.parse_args()
    if args.port:
        SERVER = "http://localhost:%d/"%args.port


def api(category, version, subcategory):
    API = "%s/api/%s/%s/"
    return API % (category, version, subcategory)


def log_failure(api, msg, response, expected_code, *args, **kwargs):
    assert response.status_code == expected_code, "FAIL:%s:%d:%s:%s:%s" % (
        msg, response.status_code, response.text, args, kwargs)


def unpack_singleton_list(possible_list):
    if isinstance(possible_list, list) and len(possible_list) == 1:
        return possible_list[0]
    else:
        print("Warn: input is not a length one list!")
        return possible_list


def validate_plot(plot):
    assert plot["data"][0:8] == '<script>', "FAIL: Plot is not a script!"
    assert plot["id"][0:3] == "vis", "FAIL: Plot does not have a vis_* id"
    assert "title" in plot, "FAIL: Plot does not have a title"
    assert "type" in plot, "FAIL: Plot does not have a type"
    return True


ANALYTICS_API_TEST = "analytics/api/0.1/analytics/"
ANALYTICS_API = api("analytics", "0.1", "analytics")
assert ANALYTICS_API == ANALYTICS_API_TEST, "generating api URLs is broken " + ANALYTICS_API + " " + ANALYTICS_API_TEST


class BedrockAPI(object):
    """BedrockAPI: a class for making calls to the Bedrock API on a remote machine"""

    def __init__(self, server, version):
        self.server = server
        self.version = version
        self.template = "%s/api/%s/%s/"

    def path(self, category, subcategory):
        return self.template % (category, self.version, subcategory)

    def endpoint(self, category, subcategory):
        endpoint = self.server + self.path(category, subcategory)
        return endpoint

    def get(self, category, path):
        return requests.get(self.endpoint(category, path))

    def post(self, category, path, *args, **kwargs):
        return requests.post(self.endpoint(category, path), *args, **kwargs)

    def list(self, category, subcategory):
        endpoint = self.endpoint(category, subcategory)
        print("Listing: %s" % endpoint)
        return requests.get(endpoint)

    def ingest(self, ingest_id):
        endpoint = self.endpoint("dataloader", "ingest/%s" % ingest_id)
        return requests.get(endpoint)

    def analytic(self, analytic_id):
        return requests.get(self.endpoint("analytics", "analytics/%s" %
                                          analytic_id))

    def put_source(self, name, ingest_id, group_name, payload):
        """Payload can be either a file or JSON structured configuration data. Returns the metadata for the new source."""
        endpoint = self.endpoint("dataloader", "sources/%s/%s/%s" %
                                 (name, ingest_id, group_name))
        print(endpoint)
        return requests.put(endpoint, files=payload)


def check_api_list(api, category, subcategory):
    resp = api.list(category, subcategory)
    assert resp.status_code == 200, "Failed to get list of %s" % subcategory
    js_list = resp.json()
    print(js_list[0])
    assert len(js_list) > 0, "Failed to download any %s" % subcategory


def check_spreadsheet(api):
    sresp = api.ingest("Spreadsheet/")
    assert sresp.status_code == 200, "Failed to load Spreadsheet"
    spreadsheet = sresp.json()
    print(spreadsheet)
    assert spreadsheet["parameters"][0][
        "value"] == ".csv,.xls,.xlsx", "Spreadsheet opal cannot read appropriate filetpes"
    return sresp


def check_pca(api):
    resp = api.analytic("Pca")
    endpoint = api.endpoint("analytics", "analytics/dimred")
    dimreds = requests.get(endpoint).json()
    assert 'Pca' in (d['analytic_id']
                     for d in dimreds), "Failed to find Pca in dimreds list"
    pprint(resp.json())
    assert resp.status_code == 200, "Failure: Pca is not installed on the server."
    return resp


def check_put(api, ssname, filename, ingest_id, group_id):
    resp = api.put_source(ssname, ingest_id, group_id,
                          {'file': open(filename, "rb")})
    pprint(resp.headers)
    created = resp.json()
    pprint(created)
    src_id = created['src_id']

    fetched = requests.get(api.endpoint("dataloader", "sources/%s" %
                                        src_id)).json()
    assert fetched['name'] == ssname, "failed to retrieve spreadsheet data"
    return created, fetched


def check_make_matrix(api, source_id, matbody):
    # echo $matbody |  http post http://192.168.33.102:81/dataloader/api/0.1/sources/$src_id/
    # postdata = json.loads(matbody)
    resp = api.post("dataloader", "sources/%s/" % source_id, json=matbody)
    assert resp.status_code == 201, "Failed to create matrix: %d: %s" % (
        resp.status_code, resp.text)
    return resp.json()


def check_analysis(api, analytic_id, source_id, postdata):
    print("INFO: creating analytic at analytics/%s/" % source_id)
    resp = api.post("analytics", "analytics/%s/" % analytic_id, json=postdata)
    assert resp.status_code == 201, "Failed to run the analytic: %d: %s: %s" % (
        resp.status_code, resp.text, analytic_id)
    return resp.json()


print("Running tests against server:%s" % SERVER)
api = BedrockAPI(SERVER, VERSION)
check_api_list(api, "analytics", "analytics")
check_api_list(api, "analytics", "analytics/clustering")
check_api_list(api, "dataloader", "ingest")
spreadsheet = check_spreadsheet(api)
check_api_list(api, "visualization", "visualization")

print("Available Analytics:")
ans = api.list("analytics", "analytics")
pca = check_pca(api)

source_name = 'iris'
group_id = 'default'

created = {}
fetched = {}
available_sources = api.list("dataloader", "sources/").json()
source_id = ""

if len(available_sources) < 4:
    created, fetched = check_put(api, source_name, "./iris.csv", "Spreadsheet",
                                 group_id)
    source_id = created['src_id']
    print("INFO: created source: %s" % source_id)
else:
    source_id = available_sources[0]['src_id']
    print("Available Sources are: %s" % (s['src_id']
                                         for s in available_sources))
    print("Not uploading new source")
    fetched = requests.get(api.endpoint("dataloader", "sources/%s/" %
                                        source_id)).json()

endpoint = api.endpoint("dataloader", "sources/%s/explore/" % source_id)
print("INFO: Getting source: %s" % endpoint)
resp = requests.get(endpoint)
matrix_id = 'iris_mtx'
matrix_name = 'iris_mtx'

feature_name_list = ['petal_length', 'petal_width', 'sepal_length', 'sepal_width', 'species']
feature_name_list_original = ['petal_length', 'petal_width', 'sepal_length', 'sepal_width', 'species']
column_types = ['Numeric', 'Numeric', 'Numeric', 'Numeric', 'String']
matbody = {'matrixFeatures': feature_name_list,
           'matrixFeaturesOriginal': feature_name_list_original,
           'matrixFilters': {'petal_length': {},
                             'petal_width': {},
                             'sepal_length': {},
                             'sepal_width': {},
                             'species': {'classname': 'TruthLabelsNumeric',
                                         'description':
                                         'Extracts the truth labels.',
                                         'filter_id': 'TruthLabelsNumeric',
                                         'input': 'Numeric',
                                         'name': 'TruthLabels',
                                         'ouptuts': ['truth_labels.csv'],
                                         'parameters': [],
                                         'possible_names': ['class', 'truth'],
                                         'stage': 'after',
                                         'type': 'extract'}},
           'matrixName': matrix_name,
           'matrixTypes': column_types,
           'sourceName': source_name}

url = api.endpoint("dataloader", "sources/%s" % (source_id))
print("INFO: Posting matrix to:%s" % url)
resp = requests.post(url, json=matbody)
log_failure(api, "posting matrix %s" % matbody, resp, 201)

mtx_res = unpack_singleton_list(check_make_matrix(api, source_id, matbody))
print("INFO: received matrix post response")
pprint(mtx_res)

analytic_id = "Pca"
# to apply the analysis to the matrix
print("INFO: creating analysis_postdata")
analysis_postdata = {
    'inputs': {'features.txt': mtx_res,
               'matrix.csv': mtx_res},
    'name': 'iris-pca',
    'parameters': [{'attrname': 'numDim',
                    'max': 15,
                    'min': 1,
                    'name': 'Dimensions',
                    'step': 1,
                    'type': 'input',
                    'value': 2}],
    'src': [mtx_res]  # this is a list because the server expects a list
}
analysis_res = check_analysis(api, analytic_id, source_id, analysis_postdata)
print("INFO: received analytic post response")
analysis_res = unpack_singleton_list(analysis_res)

print("INFO: print analysis response")
pprint(analysis_res)

viz_postdata = [mtx_res]
resp = api.post("visualization", "visualization/", json=viz_postdata)
log_failure(api, "listing visualizations", resp, 200)

plot_params_list = [{'attrname': 'x_feature',
                     'name': 'X feature index',
                     'type': 'input',
                     'value': 0}, {'attrname': 'y_feature',
                                   'name': 'Y feature index',
                                   'type': 'input',
                                   'value': 1}]
getplot_data = {'inputs':
                {'matrix.csv': analysis_res,
                 'truth_labels.csv': mtx_res},
                'parameters': plot_params_list}

plotname = "ClusterScatterTruth"
resp = api.post("visualization",
                "visualization/%s/" % plotname,
                json=getplot_data)
log_failure(api, "creating visualization %s" % plotname, resp, 200)
plot = resp.json()
validate_plot(plot)

print("INFO: Tests PASS!")

