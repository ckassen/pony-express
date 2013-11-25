from flask import Flask, jsonify

from ponyexpress.api.exceptions import *
from ponyexpress.config.configuration import *


#from ponyexpress.models.node import Node
#from ponyexpress.models.package import Package

def create_app(environment='ponyexpress.config.configuration.DevelopmentConfig'):
    app = Flask(__name__)

    # Load configuration
    #TODO: load configuration depending on environment
    app.config.from_object(environment)

    # Database
    from ponyexpress.database import db
    db.init_app(app)

    # Register blueprints
    from ponyexpress.api.v1.collector import collector
    from ponyexpress.api.v1.query import query

    app.register_blueprint(collector)
    app.register_blueprint(query)

    # Error handler
    app.register_error_handler(InvalidAPIUsage, handle_invalid_usage)

    return app


# Register error handlers
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code

    return response
