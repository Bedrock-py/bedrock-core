#****************************************************************
#  File: app.wsgi
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

import logging, sys
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '/var/www/bedrock/')
sys.path.insert(0, '/var/www/bedrock/src/')
from flask_cors import CORS
from bedrock.workflow.api import app as application

CORS(application, expose_headers='Content-Type')
