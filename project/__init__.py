import logging
import os

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy

# Initialise app
app = Flask(__name__)

# logging.basicConfig(filename='logs.log', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

# Get base directory
basedir = os.path.abspath(os.path.dirname(__file__))

# App configs
app.config['SECRET_KEY'] = 'ravenpoint'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data', 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['RESTPLUS_MASK_SWAGGER'] = False
app.config['SWAGGER_UI_DOC_EXPANSION'] = 'list'
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'files')

# CORS
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

db = SQLAlchemy(app)
Migrate(app, db)

# Import blueprints
from project.api import api, api_namespace
from project.admin.views import admin

# Define authorisations
authorisations = {
  'X-RequestDigest': {
    'type': 'apiKey',
    'in': 'header',
    'name': 'X-RequestDigest'
  }
}

# Define API
api_extension = Api(
  api,
  title='RavenPoint API',
  version='1.0',
  description='SharePoint REST API clone for testing Stack 2.0 apps - by Team Raven',
  doc='/doc',
  authorizations=authorisations
)

api_extension.add_namespace(api_namespace)

# Register blueprints
app.register_blueprint(api, url_prefix='/ravenpoint')
app.register_blueprint(admin)