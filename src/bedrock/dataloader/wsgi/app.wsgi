

import logging, sys
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '/var/www/bedrock/')
sys.path.insert(0, '/var/www/bedrock/src/')
from flask_cors import CORS
from bedrock.dataloader.api import app as application

CORS(application, expose_headers='Content-Type')
