import sys
from importlib import import_module
import logging
logging.basicConfig()
import bedrock.analytics.utils
import bedrock.dataloader.utils
import bedrock.visualization.utils
from bedrock.CONSTANTS import MONGO_HOST, MONGO_PORT, VIS_DB_NAME, VIS_COL_NAME, \
  DATALOADER_DB_NAME, DATALOADER_COL_NAME, INGEST_COL_NAME, FILTERS_COL_NAME, \
  ANALYTICS_DB_NAME, ANALYTICS_COL_NAME, RESULTS_COL_NAME
import pymongo

def manage_opals(mode, api, modulename):
    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)

    if api == 'ingest':
        col = client[DATALOADER_DB_NAME][INGEST_COL_NAME]
        if mode == 'remove':
            val = col.remove({'ingest_id': modulename})
            if val['n'] != 0:
                logging.info('    removed: %s', modulename)
                return True
            else:
                logging.warning('No registered ingest module %s.', modulename)
                return False

        elif mode == 'add':
            try:
                col.find({'ingest_id':modulename})[0]
            except IndexError:
                metadata = bedrock.dataloader.utils.get_metadata(modulename, api='ingest')
                metadata['ingest_id'] = modulename
                col.insert(metadata)
                meta = {key: value for key, value in metadata.items() if key != '_id'}
                logging.info('    added: %s', modulename)
                return True
            else:
                logging.warning('Ingest module %s is already registered.',modulename)
                return False

        if mode == 'reload':
            val = col.remove({'ingest_id':modulename})
            if val['n'] != 0:
                logging.info('    removed: %s', modulename)
            else:
                logging.warning('No registered ingest module %s.', modulename)
                return False
            try:
                col.find({'ingest_id':modulename})[0]
            except IndexError:
                metadata = bedrock.dataloader.utils.get_metadata(modulename, api='ingest')
                metadata['ingest_id'] = modulename
                col.insert(metadata)
                meta = {key: value for key, value in metadata.items() if key != '_id'}
                logging.info('    added: %s', modulename)
                return True
            else:
                logging.warning('Ingest module %s is already registered.', modulename)
                return False


    elif api == 'filters':
        col = client[DATALOADER_DB_NAME][FILTERS_COL_NAME]
        if mode == 'remove':
            val = col.remove({'filter_id':modulename})
            if val['n'] != 0:
                logging.info('    removed: %s', modulename)
                return True
            else:
                logging.warning('No registered filter %s .', modulename)
                return False

        elif mode == 'add':
            try:
                col.find({'filter_id':modulename})[0]
            except IndexError:
                metadata = bedrock.dataloader.utils.get_metadata(modulename, api='filters')
                metadata['filter_id'] = modulename
                col.insert(metadata)
                meta = {key: value for key, value in metadata.items() if key != '_id'}
                logging.info('    added: %s', modulename)
                return True
            else:
                logging.warning('WARNING: Filter %s is already registered.', modulename)
                return False

        elif mode == 'reload':
            val = col.remove({'filter_id':modulename})
            if val['n'] != 0:
                logging.info('    removed: %s', modulename)
            else:
                logging.warning('No registered filter %s.', modulename)
                return False
            try:
                col.find({'filter_id':modulename})[0]
            except IndexError:
                metadata = bedrock.dataloader.utils.get_metadata(modulename, api='filters')
                metadata['filter_id'] = modulename
                col.insert(metadata)
                meta = {key: value for key, value in metadata.items() if key != '_id'}
                logging.info('    added: %s', modulename)
                return True
            else:
                logging.warning('Filter %s is already registered.', modulename)
                return False



    elif api == 'analytics':
        col = client[ANALYTICS_DB_NAME][ANALYTICS_COL_NAME]
        if mode == 'remove':
            val = col.remove({'analytic_id':modulename})
            if val['n'] != 0:
                logging.info('    removed: %s', modulename)
                return True
            else:
                logging.warning('WARNING: No registered analytic %s.', modulename)
                return False

        elif mode == 'add':
            try:
                col.find({'analytic_id': modulename})[0]
            except IndexError:
                metadata = bedrock.analytics.utils.get_metadata(modulename)
                metadata['analytic_id'] = modulename
                col.insert(metadata)
                meta = {key: value for key, value in metadata.items() if key != '_id'}
                logging.info('    added: %s', modulename)
                return True
            else:
                logging.warning('Analytic %s is already registered.', modulename)
                return False

        elif mode == 'reload':
            val = col.remove({'analytic_id':modulename})
            if val['n'] != 0:
                logging.info('    removed: %s', modulename)
            else:
                logging.warning('No registered analytic %s .', modulename)
                return False
            try:
                col.find({'analytic_id':modulename})[0]
            except IndexError:
                metadata = bedrock.analytics.utils.get_metadata(modulename)
                metadata['analytic_id'] = modulename
                col.insert(metadata)
                meta = {key: value for key, value in metadata.items() if key != '_id'}
                logging.info('    added: %s', modulename)
                return True
            else:
                logging.warning('Analytic %s is already registered.', modulename)
                return False
    elif api == 'visualization':
        col = client[VIS_DB_NAME][VIS_COL_NAME]
        if mode == 'remove':
            val = col.remove({'vis_id':modulename})
            if val['n'] != 0:
                logging.info('    removed: %s', modulename)
                return
            else:
                logging.warning('No registered visualization %s .', modulename)
                return

        elif mode == 'add':
            try:
                col.find({'vis_id':modulename})[0]
            except IndexError:
                metadata = bedrock.visualization.utils.get_metadata(modulename)
                metadata['vis_id'] = modulename
                col.insert(metadata)
                meta = {key: value for key, value in metadata.items() if key != '_id'}
                logging.info('    added: %s', modulename)
                return
            else:
                logging.warning('Visualization %s is already registered.', modulename)
                return

        elif mode == 'reload':
            val = col.remove({'vis_id':modulename})
            if val['n'] != 0:
                logging.info('    removed: %s', modulename)
            else:
                logging.warning('No registered visualization %s.', modulename)
                return
            try:
                col.find({'vis_id':modulename})[0]
            except IndexError:
                metadata = bedrock.visualization.utils.get_metadata(modulename)
                metadata['vis_id'] = modulename
                col.insert(metadata)
                meta = {key: value for key, value in metadata.items() if key != '_id'}
                logging.info('    added: %s', modulename)
                return
            else:
                logging.warning('Visualization %s is already registered.', modulename)
                return

    else:
        print('ERROR: No api named %s.'%modulename)
