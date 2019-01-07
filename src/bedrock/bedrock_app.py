from flask import Flask
from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware
import logging, sys
from flask_cors import CORS
from bedrock.analytics.api import app as app_analytics
from bedrock.dataloader.api import app as app_dataloader
from bedrock.visualization.api import app as app_viz
from bedrock.workflow.api import app as app_workflow
# sys.path.insert(0, '/usr/local/bedrock/')
# sys.path.insert(0, '/usr/local/bedrock/src/')
logging.basicConfig(stream=sys.stderr)

analytics = CORS(app_analytics, expose_headers='Content-Type')
data_loader = CORS(app_dataloader, expose_headers='Content-Type')
viz = CORS(app_viz, expose_headers='Content-Type')
workflow = CORS(app_workflow, expose_headers='Content-Type')

app = Flask(__name__)

application = DispatcherMiddleware(app, {
    '/dataloader':     app_dataloader,
    '/analytics': app_analytics,
    '/visualization': app_viz,
    '/workflows': app_workflow
})

if __name__ == '__main__':
    run_simple('localhost', 50523, application, use_reloader=False, use_debugger=True, use_evalex=True)