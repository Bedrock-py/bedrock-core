
import sys
sys.path.insert(0, '/var/www/bedrock/')
sys.path.insert(0, '/var/www/bedrock/src/')
from bedrock.visualization.api import app as application

from flask_cors import CORS
CORS(application, expose_headers='Content-Type')
