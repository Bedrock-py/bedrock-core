#****************************************************************
#  File: configure.py
#
# Copyright (c) 2015, Georgia Tech Research Institute
# All rights reserved.
#
# This unpublished material is the property of the Georgia Tech
# Research Institute and is protected under copyright law.
# The methods and techniques described herein are considered
# trade secrets and/or confidential. Reproduction or distribution,
# in whole or in part, is forbidden except by the express written
# permission of the Georgia Tech Research Institute.
#****************************************************************/

import argparse, sys
sys.path.insert(1, '/var/www/analytics-framework/dataloader/python/')
sys.path.insert(1, '/var/www/analytics-framework/analytics/python/')
sys.path.insert(1, '/var/www/analytics-framework/visualization/python/')
sys.path.insert(1, '/var/www/analytics-framework/workflows/python/')
import DataLoader.ingest_utils
import DataLoader.filter_utils
import Analytics.analytics
import Visualization.visualization

import pymongo

MONGO_HOST = 'localhost'
MONGO_PORT = 27017
DB_DATALOADER = 'dataloader'
DB_ANALYTICS = 'analytics'
DB_VIS = 'visualization'
INGEST = 'ingest'
INGEST = 'ingest'
FILTERS = 'filters'
ANALYTICS = 'analytics'
VIS = 'visualizations'
DB_WORKFLOWS = 'workflows'
WORK = 'registered'
WORK_MOD = 'modules'



if __name__=='__main__':

    parser = argparse.ArgumentParser(description="Manually configure system's enabled/disabled modules")
    parser.add_argument('--api', action='store', required=True, metavar='api')
    parser.add_argument('--filename', action='store', required=True, metavar='filename')
    parser.add_argument('--mode', action='store', required=True, metavar='mode')
    args = parser.parse_args()

    #get the appropriate client
    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)

    if args.api == 'ingest':
        col = client[DB_DATALOADER][INGEST]
        if args.mode == 'remove':
            val = col.remove({'ingest_id':args.filename})
            if val['n'] != 0:
                print 'REMOVED:', args.filename
                exit(0)
            else:
                print 'WARNING: No registered ingest module with that name.'
                exit(0)

        elif args.mode == 'add':
            try:
                col.find({'ingest_id':args.filename})[0]
            except IndexError:
                metadata = DataLoader.ingest_utils.get_metadata(args.filename)
                metadata['ingest_id'] = args.filename
                col.insert(metadata)
                meta = {key: value for key, value in metadata.items() if key != '_id'}
                print 'ADDED: ', args.filename
                exit(0)
            else:
                print 'WARNING: Ingest module with that name is already registered.'
                exit(0)
        
        if args.mode == 'reload':
            val = col.remove({'ingest_id':args.filename})
            if val['n'] != 0:
                print 'REMOVED:', args.filename
            else:
                print 'WARNING: No registered ingest module with that name.'
                exit(0)
            try:
                col.find({'ingest_id':args.filename})[0]
            except IndexError:
                metadata = DataLoader.ingest_utils.get_metadata(args.filename)
                metadata['ingest_id'] = args.filename
                col.insert(metadata)
                meta = {key: value for key, value in metadata.items() if key != '_id'}
                print 'ADDED: ', args.filename
                exit(0)
            else:
                print 'WARNING: Ingest module with that name is already registered.'
                exit(0)


    elif args.api == 'filters':
        col = client[DB_DATALOADER][FILTERS]
        if args.mode == 'remove':
            val = col.remove({'filter_id':args.filename})
            if val['n'] != 0:
                print 'REMOVED:', args.filename
                exit(0)
            else:
                print 'WARNING: No registered filter with that name.'
                exit(0)

        elif args.mode == 'add':
            try:
                col.find({'filter_id':args.filename})[0]
            except IndexError:
                metadata = DataLoader.filter_utils.get_metadata(args.filename)
                metadata['filter_id'] = args.filename
                col.insert(metadata)
                meta = {key: value for key, value in metadata.items() if key != '_id'}
                print 'ADDED: ', args.filename
                exit(0)
            else:
                print 'WARNING: Filter with that name is already registered.'
                exit(0)

        elif args.mode == 'reload':
            val = col.remove({'filter_id':args.filename})
            if val['n'] != 0:
                print 'REMOVED:', args.filename
            else:
                print 'WARNING: No registered filter with that name.'
                exit(0)
            try:
                col.find({'filter_id':args.filename})[0]
            except IndexError:
                metadata = DataLoader.filter_utils.get_metadata(args.filename)
                metadata['filter_id'] = args.filename
                col.insert(metadata)
                meta = {key: value for key, value in metadata.items() if key != '_id'}
                print 'ADDED: ', args.filename
                exit(0)
            else:
                print 'WARNING: Filter with that name is already registered.'
                exit(0)



    elif args.api == 'analytics':
        col = client[DB_ANALYTICS][ANALYTICS]
        if args.mode == 'remove':
            val = col.remove({'analytic_id':args.filename})
            if val['n'] != 0:
                print 'REMOVED:', args.filename
                exit(0)
            else:
                print 'WARNING: No registered analytic with that name.'
                exit(0)

        elif args.mode == 'add':
            try:
                col.find({'analytic_id':args.filename})[0]
            except IndexError:
                exec("import Analytics.algorithms." + args.filename)
                metadata = Analytics.analytics.get_metadata(args.filename)
                metadata['analytic_id'] = args.filename
                col.insert(metadata)
                meta = {key: value for key, value in metadata.items() if key != '_id'}
                print 'ADDED: ', args.filename
                exit(0)
            else:
                print 'WARNING: Analytic with that name is already registered.'
                exit(0)

        elif args.mode == 'reload':
            val = col.remove({'analytic_id':args.filename})
            if val['n'] != 0:
                print 'REMOVED:', args.filename
            else:
                print 'WARNING: No registered analytic with that name.'
                exit(0)
            try:
                col.find({'analytic_id':args.filename})[0]
            except IndexError:
                exec("import Analytics.algorithms." + args.filename)
                metadata = Analytics.analytics.get_metadata(args.filename)
                metadata['analytic_id'] = args.filename
                col.insert(metadata)
                meta = {key: value for key, value in metadata.items() if key != '_id'}
                print 'ADDED: ', args.filename
                exit(0)
            else:
                print 'WARNING: Analytic with that name is already registered.'
                exit(0)

    elif args.api == 'workflows':
        col = client[DB_WORKFLOWS][WORK_MOD]
        if args.mode == 'remove':
            val = col.remove({'workflow_id':args.filename})
            if val['n'] != 0:
                print 'REMOVED:', args.filename
                exit(0)
            else:
                print 'WARNING: No registered workflow with that name.'
                exit(0)

        elif args.mode == 'add':
            try:
                col.find({'workflow_id':args.filename})[0]
            except IndexError:
                exec("import Workflows.work." + args.filename)
                metadata = Workflows.workflows.get_metadata(args.filename)
                metadata['workflow_id'] = args.filename
                col.insert(metadata)
                meta = {key: value for key, value in metadata.items() if key != '_id'}
                print 'ADDED: ', args.filename
                exit(0)
            else:
                print 'WARNING: Workflow with that name is already registered.'
                exit(0)

        elif args.mode == 'reload':
            val = col.remove({'work_id':args.filename})
            if val['n'] != 0:
                print 'REMOVED:', args.filename
            else:
                print 'WARNING: No registered workflow with that name.'
                exit(0)
            try:
                col.find({'work_id':args.filename})[0]
            except IndexError:
                exec("import Workflows.work." + args.filename)
                metadata = Workflows.workflows.get_metadata(args.filename)
                metadata['work_id'] = args.filename
                col.insert(metadata)
                meta = {key: value for key, value in metadata.items() if key != '_id'}
                print 'ADDED: ', args.filename
                exit(0)
            else:
                print 'WARNING: Workflow with that name is already registered.'
                exit(0)


    elif args.api == 'visualization':
        col = client[DB_VIS][VIS]
        if args.mode == 'remove':
            val = col.remove({'vis_id':args.filename})
            if val['n'] != 0:
                print 'REMOVED:', args.filename
                exit(0)
            else:
                print 'WARNING: No registered visualization with that name.'
                exit(0)

        elif args.mode == 'add':
            try:
                col.find({'vis_id':args.filename})[0]
            except IndexError:
                exec("import Visualization.vis." + args.filename)
                metadata = Visualization.visualization.get_metadata(args.filename)
                metadata['vis_id'] = args.filename
                col.insert(metadata)
                meta = {key: value for key, value in metadata.items() if key != '_id'}
                print 'ADDED: ', args.filename
                exit(0)
            else:
                print 'WARNING: Visualization with that name is already registered.'
                exit(0)
        
        elif args.mode == 'reload':
            val = col.remove({'vis_id':args.filename})
            if val['n'] != 0:
                print 'REMOVED:', args.filename
            else:
                print 'WARNING: No registered visualization with that name.'
                exit(0)
            try:
                col.find({'vis_id':args.filename})[0]
            except IndexError:
                exec("import Visualization.vis." + args.filename)
                metadata = Visualization.visualization.get_metadata(args.filename)
                metadata['vis_id'] = args.filename
                col.insert(metadata)
                meta = {key: value for key, value in metadata.items() if key != '_id'}
                print 'ADDED: ', args.filename
                exit(0)
            else:
                print 'WARNING: Visualization with that name is already registered.'
                exit(0)

    else:
        print 'ERROR: No api by that name.'
