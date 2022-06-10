import json
import os
import pandas as pd
import sqlite3

from flask import Blueprint, request
from flask_restx import Namespace, Resource, fields
from project import db, app
from project.utils import get_all_table_names
from werkzeug.exceptions import BadRequest

# Create blueprint
api = Blueprint(
  'api', __name__,
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
  @api_namespace.response(400, 'Bad request: List does not exist.')
  @api_namespace.response(500, 'Internal Server Error')
  def get(self, list_id):
    '''RavenPoint list properties endpoint'''
    
    # Extract URL params
    params = {'listId': list_id}
    for k, v in request.args.items():
      if k not in ['$select', '$filter', '$expand']:
        raise BadRequest('Invalid keyword. Use only $select, $filter, or $expand.')
      params[k] = v
    
    # Check that all query options have parameters
    if any([v is None or len(v) == 0 for v in params.values()]):
      raise BadRequest(
        'Invalid parameters. Check values for your query options (e.g. $select, $filter, $expand).'
      )

    # Check if main list exists
    with sqlite3.connect(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')) as conn:
      all_tables = get_all_table_names(conn)
    if list_id not in all_tables.id.tolist():
      raise BadRequest('List does not exist.')

    # Extract table metadata
    curr_table = all_tables.loc[all_tables.id.eq(list_id)].to_dict('records')[0]
    params['table_name'] = curr_table['table_name']
    params['table_db_name'] = curr_table['table_db_name']

    # If no params are given, return 10 rows of data
    if not params.get('$select') and not params.get('$filter') and not params.get('$expand'):
      with sqlite3.connect(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')) as conn:
        df = pd.read_sql(f"SELECT * FROM {params['table_db_name']} LIMIT 10", conn)
      return {
        'message': 'No query keywords found. Returning first 10 rows.',
        'value': df.to_dict('records')
      }
    
    # Get all tables in query
    query_tables = [params['table_db_name']]
    if '$expand' in params.keys():
      query_tables.extend(params['$expand'].split(','))
    
    # Check that all other tables exist
    # if len(query_tables) > 1:
    #   for table in query_tables[1:]:
    #     if table not in all_tables.table_db_name.tolist():
    #       raise BadRequest(f"{table} does not exist.")

    # Process fields selected
    return_cols = []
    if '$select' in params.keys():
      # Check for ListItemEntityTypeFullName
      if params['$select'] == 'ListItemEntityTypeFullName':
        table_pascal = curr_table['table_db_name'].title().replace('_', '')
        return {'d': f'SP.Data.{table_pascal}ListItem'}
    
      # Extract columns, processing expanded tables (if any)
      select_params = params['$select'].replace(' ', '').split(',')
      
      for col in select_params:
        # A forward slash indicates another table exists - extract it
        if '/' in col:
          join_table, join_col = col.split('/')
          # Only add tableName.colName if that table is specified in the expand keyword
          if join_table in query_tables:
            return_cols.append(f"{join_table}.{join_col}")
        else:
          return_cols.append(f"{curr_table['table_db_name']}.{col}")



    # Update params
    params['columns'] = return_cols
    params['query_tables'] = query_tables
    
    output = f"SELECT {', '.join(params['columns'])} \
FROM {curr_table['table_db_name']} \
INNER JOIN "
    params['sql_query'] = output
    return params
