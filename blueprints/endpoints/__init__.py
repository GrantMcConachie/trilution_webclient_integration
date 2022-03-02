# Adds documentation api as well as url_prefix for api
from flask import Blueprint
from flask_restx import Api
from blueprints.endpoints.sampledata import namespace as sampledata_ns
from blueprints.endpoints.samplelist import namespace as samplelist_ns
from blueprints.endpoints.QCreceive import namespace as QCreceive_ns
from blueprints.endpoints.webfront import namespace as webfront_ns


# Declareing the blueprint to be used for the app
# Includes the url prefix
blueprint = Blueprint('gilson_REST', __name__, url_prefix='/gilson_REST')

# API for documentation use localhost/gilson_REST/doc to access
api_extension = Api(
    blueprint,
    title='Gilson REST endpoint documentation',
    doc='/doc'
)

# adds namespaces to the api
api_extension.add_namespace(sampledata_ns)
api_extension.add_namespace(samplelist_ns)
api_extension.add_namespace(QCreceive_ns)
api_extension.add_namespace(webfront_ns)