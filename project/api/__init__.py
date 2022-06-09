import os
import pandas as pd

from collections import defaultdict
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

# Endpoint for getting list items
@api_namespace.route(
  "/web/Lists(guid'<string:list_id>')/items",
  doc={'description': '''Endpoint for interacting with simulated List (SQLite database). \
Currently implemented URL params: `filter`, `select`, and `expand`.

- Use `$select=ListItemEntityTypeFullName` to get the List item entity type.
- Use `$select=<columns>` to select columns.
- Use `$filter=<criteria>` to filter items.
- Use `$expand=<lookup_table>` to join tables.
  '''})
@api_namespace.doc(params={'list_id': 'Simulated SP List ID'})
class ListItems(Resource):
  @api_namespace.response(200, 'Success: Returns requested list items or properties.')
  @api_namespace.response(500, 'Internal Server Error')
  def get(self, list_id):
    '''RavenPoint list properties endpoint'''
    # Extract URL params
    params = {'listId': list_id}
    for k, v in request.args.items():
      assert k in ['$select', '$filter', '$expand'], 'Use only keywords $select, $filter, $expand.'
      params[k] = v
    expand_tables = []
    if '$expand' in params.keys():
      expand_tables = params['$expand'].split(',')
    if '$select' in params.keys():
      # Check for ListItemEntityTypeFullName
      if params['$select'] == 'ListItemEntityTypeFullName':
        return {'d': 'SP.Data.FakeDataListItem'}
      
      # Extract columns, processing expanded tables (if any)
      select_params = params['$select'].split(',')
      return_cols = []
      joined_fields = defaultdict(list)
      for col in select_params:
        if '/' in col:
          join_table, join_col = col.split('/')
          if '/' in join_table:
            join_table = join_table.split('/')[0]
          # Only add tableName.colName if that table is specified in the expand keyword
          joined_fields[join_table].append(join_col)
        else:
          return_cols.append(col)

      params['columns'] = return_cols
      params['expand_tables'] = expand_tables
      params['joined_fields'] = joined_fields
    return params
