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

import sys
sys.path.insert(0, '/var/www/bedrock/')
sys.path.insert(0, '/var/www/bedrock/src/')
from bedrock.visualization.api import app as application

from flask_cors import CORS
CORS(application, expose_headers='Content-Type')
