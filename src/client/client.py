"""BedrockAPI client is a python class that represents a Bedrock Server
and makes it easier to make requests and handle the responses.

This module represents a layer of stability for client applications.
A web app for using the Bedrock functionality should use this library
for interacting with the bedrock server so that the details of constructing
the json requests can be handled here rather than in each client.

The idea is to expose the web api as an object that has methods for making the requests
and returning the responses as python objects.

"""
import logging
import requests

logging.basicConfig(
    format='%(levelname)s: %(asctime)s: %(message)s', level=logging.INFO)


class BedrockAPI(object):
    """BedrockAPI: a class for making calls to the Bedrock API on a remote machine"""

    def __init__(self, server, version):
        self.server = server
        self.version = version
        self.template = "%s/api/%s/%s/"

    def path(self, category, subcategory):
        """form a path for accessing apis at category, subcategory."""
        return self.template % (category, self.version, subcategory)

    def endpoint(self, category, subcategory):
        """form a url endpoint for accessing resources in category/subcategory"""
        endpoint = self.server + self.path(category, subcategory)
        return endpoint

    def get(self, category, path):
        """make a get request using requests"""
        return requests.get(self.endpoint(category, path))

    def post(self, category, path, *args, **kwargs):
        """make a post request using requests"""
        return requests.post(self.endpoint(category, path), *args, **kwargs)

    def list(self, category, subcategory):
        """List the resourdes available in category/subcategory.

        For example: api.list('analytics', 'classification')"""
        endpoint = self.endpoint(category, subcategory)
        logging.info("Listing: %s", endpoint)
        return requests.get(endpoint)

    def ingest(self, ingest_id):
        """find a dataloader ingest resource with id ingest_id."""
        endpoint = self.endpoint("dataloader", "ingest/%s" % ingest_id)
        return requests.get(endpoint)

    def analytic(self, analytic_id):
        """find an analytic with resource id analytic_id"""
        return requests.get(
            self.endpoint("analytics", "analytics/%s" % analytic_id))

    def visualization(self, viz_id):
        """find an visualization with resource id viz_id"""
        return requests.get(
            self.endpoint("visualization", "visualization/%s" % viz_id))

    def put_source(self, name, ingest_id, group_name, payload):
        """Payload can be either a file or JSON structured configuration data.
        Returns the metadata for the new source."""
        endpoint = self.endpoint("dataloader", "sources/%s/%s/%s" %
                                 (name, ingest_id, group_name))
        logging.info('putting source to: %s', endpoint)
        return requests.put(endpoint, files=payload)
