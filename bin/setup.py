#!/usr/bin/env python
'''
setup.py: prepare the current bedrock server for testing.
You can call this script to set up the server by resetting
it to the blank state and installing the necessary opal packages.

The apache service is restarted so that changes to the webapp are visible
to clients.

Exits with 1 and uncaught exception if an install fails
Exits with 0 if successful.
'''
import subprocess
import os.path
import sys
import time

def service_wait(max_retries, interval, testfun):
    for i in range(max_retries):
        if testfun(i):
            return True
        else:
            time.sleep(interval)
    return False

MONGO_LOG = "/var/log/mongodb/mongodb.log"
if __name__ == "__main__":
    # crappy check that mongo is running
    # if the log file is not there then it has never been started.
    # TODO make this check test availability of the connections.
    subprocess.check_call('service mongodb start  &&  /usr/sbin/apache2ctl start', shell=True)
    if not service_wait(10, 1, lambda x: os.path.exists(MONGO_LOG)):
        print("mongo not running yet")
        sys.exit(1)

    subprocess.check_call('opal reset', shell=True)
    pkgs = ['opal-dataloader-ingest-spreadsheet',
            'opal-dataloader-ingest-omop',
            'opal-dataloader-ingest-sql',
            'opal-analytics-dimensionreduction',
            'opal-analytics-clustering',
            'opal-dataloader-filter-truth',
            'opal-visualization-scatterplot']
    for package in pkgs:
        subprocess.check_call('opal install %s'% package, shell=True)
    # we just stop the apache2 server with apache2ctrl because we started it
    # in the Dockerfile with apache2ctrl start -D FOREGROUND
    # TODO if you set up process management correctly, change this line.
    # subprocess.check_call('sudo apache2ctl stop', shell=True)
