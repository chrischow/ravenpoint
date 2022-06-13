import json
import os
import pandas as pd
import sqlite3

from flask import Blueprint, request
from flask_restx import Namespace, Resource, fields
from project import db, app
from project.utils import get_all_table_names, get_all_relationships, parse_odata_filter, \
  parse_odata_query
from werkzeug.exceptions import BadRequest

# Create blueprint
api = Blueprint(
  'api', __name__,
  template_folder='api_templates'
)

# Connection string
conn_string = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')

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

# Endpoint for list metadata
@api_namespace.route(
  "/web/Lists(guid'<string:list_id>')",
  doc={'description': '''Endpoint for getting List metadata. Use `$select` to choose \
    specific metadata fields to retrieve. Options are `Id`, `ListItemEntityTypeFullName`, \
    `table_name` (RavenPoint only) and `table_db_name` (RavenPoint only).'''}
)
@api_namespace.doc(params={'list_id': 'Simulated SP List ID'})
class ListMetadata(Resource):
  @api_namespace.response(200, 'Success: Returns List metadata')
  @api_namespace.response(400, 'Bad request: Invalid query.')
  @api_namespace.response(500, 'Internal Server Error')
  
  def get(self, list_id):
    '''RavenPoint list metadata endpoint'''
    
    # Check if list exists
    with sqlite3.connect(conn_string) as conn:
      all_tables = get_all_table_names(conn)
    if list_id not in all_tables.id.tolist():
      raise BadRequest('List does not exist.')
    
    # Extract URL params
    params = {'listId': list_id}
    for k, v in request.args.items():
      if k not in ['$select', '$filter', '$expand']:
        raise BadRequest('Invalid keyword. Use only $select, $filter, or $expand.')
      params[k] = v

    # Get metadata
    table = all_tables \
        .rename(columns={'id': 'Id'}) \
        .loc[all_tables.id.eq(list_id)].to_dict('records')[0]
    table_pascal = table['table_db_name'].title().replace('_', '')
    table['ListItemEntityTypeFullName'] = f'SP.Data.{table_pascal}ListItem'

    # Return all if no specified fields specified
    if '$select' not in params.keys():
        return {'d': table}
    
    # Extract requested fields
    fields = params['$select'].split(',')
    fields = [field.strip() for field in fields]
    if any([field not in ['ListItemEntityTypeFullName', 'Id', 'table_name', 'table_db_name'] for field in fields]):
      raise BadRequest('Invalid metadata property. Options: ListItemEntityTypeFullName, Id, table_name, table_db_name.')
    
    output  = {'Id': table['Id']}
    for field in fields:
      output[field] = table[field]

    return {'d': output}


# Endpoint for getting list items
@api_namespace.route(
  "/web/Lists(guid'<string:list_id>')/items",
  doc={'description': '''Endpoint for retrieving List items. \
Currently implemented URL params: `filter`, `select`, and `expand`.

- Use `$select=ListItemEntityTypeFullName` to get the List item entity type.
- Use `$select=<columns>` to select columns.
- Use `$filter=<criteria>` to filter items.
- Use `$expand=<lookup_table>` to join tables.
  '''})
@api_namespace.doc(params={'list_id': 'Simulated SP List ID'})
class ListItems(Resource):
  @api_namespace.response(200, 'Success: Returns requested list items or properties.')
  @api_namespace.response(400, 'Bad request: Invalid query.')
  @api_namespace.response(500, 'Internal Server Error')
  def get(self, list_id):
    '''RavenPoint list items endpoint'''
    
    # Check for invalid keywords
    request_keys = request.args.keys()
    if any([key not in ['$select', '$filter', '$expand'] for key in request_keys]):
      raise BadRequest('Invalid keyword(s). Use only $select, $filter, or $expand.')
    
    # Extract URL params
    params = parse_odata_query(request.args)
    if params:
      params['listId'] = list_id

    # Check that all query options have parameters
    # if any([v is None or len(v) == 0 for v in params.values()]):
    #   raise BadRequest(
    #     'Invalid value(s). Check values for your query options (e.g. $select, $filter, $expand).'
    #   )

    # Check if list exists; get all relationships
    with sqlite3.connect(conn_string) as conn:
      all_tables = get_all_table_names(conn)
      all_rships = get_all_relationships(conn)
    if list_id not in all_tables.id.tolist():
      raise BadRequest('List does not exist.')

    # Extract table metadata
    curr_table = all_tables.loc[all_tables.id.eq(list_id)].to_dict('records')[0]
    curr_db_table = curr_table['table_db_name']

    # If no params are given, return all data
    if '$select' not in request_keys and '$filter' not in request_keys and '$expand' not in request_keys:
      with sqlite3.connect(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')) as conn:
        df = pd.read_sql(f"SELECT * FROM {curr_db_table}", conn)
      return {
        'listId': list_id,
        'value': df.to_dict('records')
      }
    
    # EXPAND - Get all tables in query
    joins = {}
    for col in params['expand_cols']:
      # Check if the column to expand was included in the selected columns
      if not any([col in join_col for join_col in params['join_cols']]):
        raise BadRequest(f'Expand column `{col}` not specified in selected columns.')
      
      # Add the Id column
      if not any([f'{col}/Id' in join_col for join_col in params['join_cols']]):
        params['join_cols'] = [f'{col}/Id'] + params['join_cols']
      print(curr_db_table, col)
      rship = all_rships.loc[all_rships.table_left.eq(curr_db_table) & \
        all_rships.table_left_on.eq(col)]
      if rship.shape[0] == 0:
        raise BadRequest(f"Relationship from field '{col}' does not exist.")
      else:
        joins[col] = {
          'table': rship.table_lookup.iloc[0],
          'table_pk': rship.table_lookup_on.iloc[0]
        }

    # Process joins data
    for i, col in enumerate(params['join_cols']):
      lookup_col, lookup_table_col = col.split('/')
      if not lookup_col in params['expand_cols']:
        raise BadRequest(f'Lookup field {lookup_col} not specified in $expand parameter.')
      params['join_cols'][i] = params['join_cols'][i].replace(
        lookup_col + '/', joins[lookup_col]['table'] + '.'
      )

    # Process filter
    params['filter_query'] = parse_odata_filter(params['filter_query'], joins)

    # Add aliases to lookup tables
    select_aliases = [f"{curr_db_table}.{col}" for col in params['main_cols']] + \
      [f"{col} AS '{col.replace('.', '__')}'" for col in params['join_cols']]
    
    # Prepare SQL query
    sql_query = []
    sql_query.append(f"SELECT {', '.join(select_aliases)}")
    sql_query.append(f"FROM {curr_db_table}")
    conn = sqlite3.connect(conn_string)

    for expand_col, lookup_data in joins.items():
      sql_query.append(f"INNER JOIN {lookup_data['table']}" + \
        f" ON {curr_db_table}.{expand_col} = {lookup_data['table']}.{lookup_data['table_pk']}")

    sql_query.append(f"WHERE {params['filter_query']}")

    # Query database and process data
    data = pd.read_sql(' '.join(sql_query), con=conn)
    nested_cols = data.columns[data.columns.str.contains('__', regex=False)]
    nested_cols = list(set([col.split('__')[0] for col in nested_cols]))
    for nested_col in nested_cols:
      sub_cols = data.columns[data.columns.str.contains(nested_col + '__')]
      data[nested_col] = data[sub_cols].apply(lambda x: {k.replace(f'{nested_col}__', ''): v for k, v in zip(x.index, x.values)}, axis=1)
      data = data.drop(sub_cols, axis=1)

    # print(data)
    conn.close()

    # Update params
    params['sql_query'] = ' '.join(sql_query)

    return { 'diagnostics': params,
    'value': data.to_dict('records') }
