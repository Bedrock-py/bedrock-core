# coding: utf-8

# Gallup Cycle 2 Analysis Strata Notebook
# The components (opals) used in this notebook were based on analysis scripts written by Pablo Diego-Rosales, PhD, Gallup Inc.
# This scaffolding script was written by Scott Appling, GTRI


# Goals - Demonstrate Cycle 2 Opals
# Notes: The cycle 2 scripts were written as a pipeline within R that requires setting many global variables in the R workspace;
# To reduce time spent replicating variables in and out of R, the R Workspace is saved itself between the Opals that form the workflow
# Future TODO: Create and design an Opal middleware for running R Workspace-based opals to aggregate and consolidate some current code

from bedrock.client.client import BedrockAPI

# ### Test Connection to Bedrock Server
#
# This code assumes a local bedrock is hosted at localhost on port 81.  Change the `SERVER` variable to match your server's URL and port.

SERVER = "http://localhost:50523/"
api = BedrockAPI(SERVER)


# resp = api.put_source('VS_Game_Analysis1', ingest_id, 'testGroup1', {}, {"url": analysis_files_url})
name = "TestWorkflow1" # use your own unique testing name
group_name = "testGroup2" # use your own group name or "overwrite" to re-download existing files

# Step 1. Retrieve game logs from an OSF folder
ingest_id = 'opals.cycle2_1_load.Load.Load'
# Original Node - https://api.osf.io/v2/nodes/5wvys/
# analysis_files_url = "https://api.osf.io/v2/nodes/5wvys/files/osfstorage/5bfbf78f2885c40019112d84/"
analysis_files_url2 = "https://api.osf.io/v2/nodes/5wvys/files/osfstorage/5beb30e59ebb7b0017be253b/?format=json"

# Use the loading/ingest method of the Load opal
resp = api.put_source(name, ingest_id, group_name, {}, {"url": analysis_files_url2})
src_id = resp.json()["src_id"]
# debug - src_id = 'd3e1b246f5ca44b2a682a09a93c561f1'

# Step 2. Run Effects.R on the downloaded files using the custom/initialize method of the Load opal
resp = api.post("dataloader/sources/" + src_id, "custom/initialize")

# Step 3. Load the wrangle opal and run
analytic_id = "opals.cycle2_2_wrangle.Wrangle.Wrangle"
resp = api.post("analytics/analytics", "{}/custom/{}/run".format(analytic_id, src_id))
# Note: No results produced for this step but changes are saved in R_Workspace afterwards

# Step 4. Load the Analytics Opal and run
# Get results of GLMM are below - This step takes a good bit of time because all game logs are currently being downloaded from single OSF folder

analytic_id = "opals.cycle2_3_analytics.Analytics.Analytics"
resp = api.post("analytics/analytics", "{}/custom/{}/run".format(analytic_id, src_id))
# debug - resp_id = 'd46c7dc5732245cc96f4ffcb77ab7c3f'

# Debug
# resp.json()['id']
# test - resp_id = 'c7915228880e4aeea21a38be2f7dfe19'

# To get a sample output - the results of GLMM
# output = api.download_results_matrix(src_id, resp_id, 'matrix.csv')

# Step 5. Run active learning and get rankings
analytic_id = "opals.cycle2_4_active_learning.ActiveLearning.ActiveLearning"
resp = api.post("analytics/analytics", "{}/custom/{}/run".format(analytic_id, src_id))
# res = 'f878cdf50f484d8d8385dc240eb1430b'
# resp.json()['id']

# Example - to get output - the results of active learning
# output = api.download_results_matrix(src_id, 'f878cdf50f484d8d8385dc240eb1430b', 'matrix.csv')

# Step 6. Run hypothesis testing and get predictions / test results
# Note: dependent on the hypotheses present in the data files downloaded - without all hypotheses in game logs url, could not work

analytic_id = "opals.cycle2_5_hypothesis_testing.HypothesisTesting.HypothesisTesting"
resp = api.post("analytics/analytics", "{}/custom/{}/run".format(analytic_id, src_id))

# Get results of hypothesis testing
# output = api.download_results_matrix(src_id, resp['id'], 'matrix.csv')