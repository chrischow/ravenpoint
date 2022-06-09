import os
import pandas as pd

from project import db
from flask import Blueprint, request
from flask_restplus import Namespace, Resource, fields

# Create blueprint
api = Blueprint(
  'admin', __name__,
  template_folder='api_templates'
)

# Create namespace
api_namespace = Namespace('_api', 'RavenPoint REST API endpoints')

hello_world_model = api_namespace.model(
  'Hello World', {
    'message': fields.String(
      readonly=True,
      description='Hello World message'
    )
  }
)

hello_world_example = {'message': 'Hello World!'}

@api_namespace.route('')
class HelloWorld(Resource):

  @api_namespace.marshal_list_with(hello_world_model)
  @api_namespace.response(500, 'Internal Server Error')
  def get(self):
    '''Hello world message endpoint'''
    return hello_world_example

# Endpoint for request digest value
x_req_digest_model = api_namespace.model(
  'XRequestDigestModel', {
    'response': fields.String(
      readonly=True,
      description='Returns a simulated X-Request digest value with no expiry.'
    )
  }
)

@api_namespace.route('/contextinfo')
class XRequestDigestValue(Resource):
  @api_namespace.marshal_list_with(
    x_req_digest_model,
    description='Success: Returns a simulated X-Request digest value with no expiry.')
  @api_namespace.response(500, 'Internal Server Error')
  def post(self):
    '''X-Request Digest Value endpoint'''
    return {'response': '1111-2222-3333-4444'}

# Endpoint for list item entity type full name
list_item_entity_fields = api_namespace.model(
  'ListItemEntityFullName', {
    'ListItemEntityTypeFullName': fields.String(
      readonly=True,
      description="Returns the supplied list's (fake) ListItemEntityTypeFullName."
    )
  }
)

list_item_entity_type_full_name_model = api_namespace.model(
  'ListItemEntityType', {
    'd': fields.Nested(list_item_entity_fields)
  }
)

@api_namespace.route("/web/Lists(guid'<string:list_id>')$select=ListItemEntityTypeFullName")
@api_namespace.doc(params={'list_id': 'Simulated SP List ID'})
class ListItemEntityTypeFullName(Resource):
  @api_namespace.marshal_list_with(
    list_item_entity_type_full_name_model,
    description="Success: Returns the supplied list's (fake) ListItemEntityTypeFullName."
  )
  @api_namespace.response(500, 'Internal Server Error')
  def get(self, list_id):
    '''ListItemEntityTypeFullName endpoint'''
    return {'d': {'ListItemEntityTypeFullName': 'FakeDatasetListItem'}}

# Endpoint for getting list items
list_item_fields = api_namespace.model(
  'ListItemFields', {
    'data': fields.List(fields.String)
  }
)
@api_namespace.route(
  "/web/Lists(guid'<string:list_id>')/items",
  doc={'description': 'Endpoint for interacting with simulated List (SQLite database). \
    Currently implemented URL params: `filter` and `select`.'})
@api_namespace.doc(params={'list_id': 'Simulated SP List ID'})
class ListItems(Resource):
  @api_namespace.response(200, 'Success: Returns data.')
  @api_namespace.response(500, 'Internal Server Error')
  def get(self, list_id):
    '''RavenPoint list items endpoint'''
    print(request.args)
    return {'data': list_id }
