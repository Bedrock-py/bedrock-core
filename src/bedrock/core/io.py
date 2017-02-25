"""io.py provides io operations to the bedrock apis.
This will allow bedrock to support data stored in HDFS, on remote clusters, and over web apis.
"""
import os
import json
from bedrock.CONSTANTS import *
import werkzeug

DIRMASK = 0o775


def write_source_file(dataloader_path, src_id, uploadedfile):
    """Writes the a dataloader source into a file from web request file upload."""
    rootpath = os.path.join(dataloader_path, src_id, 'source/')
    filename = werkzeug.secure_filename(uploadedfile.filename)
    if not os.path.exists(rootpath):
        os.makedirs(rootpath, DIRMASK)
    filepath = os.path.join(rootpath, filename)
    uploadedfile.save(filepath)
    return rootpath, filepath


def write_source_config(dataloader_path, src_id, conn_info):
    """Writes the configuration data for a dataloader source into a file"""
    diroriginal = os.path.join(dataloader_path, src_id, 'source/')
    os.makedirs(diroriginal, DIRMASK)
    filepath = os.path.join(diroriginal, 'conf.json')
    with open(filepath, 'w') as outfile:
        json.dump(conn_info, outfile)
    return diroriginal, filepath
