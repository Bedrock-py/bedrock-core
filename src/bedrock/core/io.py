"""io.py provides io operations to the bedrock apis.
This will allow bedrock to support data stored in HDFS, on remote clusters, and over web apis.
"""
import os
import json
from multiprocessing.pool import Pool

from bedrock.CONSTANTS import *
import werkzeug
import requests

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



def d_file_helper(p_items):
    filepath, local_filename = download_file(p_items[0], p_items[1], p_items[2])
    return filepath

def write_source_files_web(dataloader_path, src_id, names_urls):
    """Writes multiple files downloaded from a web source"""

    rootpath = os.path.join(dataloader_path, src_id, 'source/')
    if not os.path.exists(rootpath):
        os.makedirs(rootpath, DIRMASK)

    filepaths = []
    pool = Pool(processes=4)

    filepaths = pool.map(d_file_helper, list(map(lambda x: (rootpath, x[0], x[1]), names_urls)))
    return rootpath, filepaths


def download_file(rootpath, name, url):
    local_filename = name
    r = requests.get(url, stream=True)
    filepath = rootpath + local_filename
    with open(filepath, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                # f.flush()
    r.close()
    return filepath, local_filename


def write_source_config(dataloader_path, src_id, conn_info):
    """Writes the configuration data for a dataloader source into a file"""
    diroriginal = os.path.join(dataloader_path, src_id, 'source/')
    os.makedirs(diroriginal, DIRMASK)
    filepath = os.path.join(diroriginal, 'conf.json')
    with open(filepath, 'w') as outfile:
        json.dump(conn_info, outfile)
    return diroriginal, filepath
