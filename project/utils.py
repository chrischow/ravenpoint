# RAVENPOINT UTILITIES
import pandas as pd
import re
import sqlite3

from project import app
from wtforms import ValidationError

# Get all tables in database
def get_all_table_names(conn):
  df = pd.read_sql(
    'SELECT * from tables',
    conn
  )
  return df

# Get all table metadata
def get_all_table_metadata(conn, tables):
  nrows = []
  all_columns = []
  for table_name in tables.table_db_name:
      # Get columns
      cursor = conn.execute(f"SELECT * FROM {table_name}")
      columns = ', '.join(list(map(lambda x: x[0], cursor.description)))
      all_columns.append(columns)

      # Get no. of rows
      cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
      table_nrows = cursor.fetchone()[0]
      nrows.append(table_nrows)
  output = tables.copy()
  output['nrows'] = nrows
  output['columns'] = all_columns
  return output

# Get all relationships in database
def get_all_relationships(conn):
  df = pd.read_sql(
    'SELECT * FROM relationships',
    conn
  )
  return df

def translate_odata(database_uri, table_name, odata_query):
  from odata_query.sqlalchemy import apply_odata_query
  from sqlalchemy import create_engine, MetaData, Table
  from sqlalchemy.orm import mapper, sessionmaker
  from sqlalchemy.dialects import sqlite

  # Autoload model
  class TempTable():
    pass

  engine = create_engine(database_uri)
  metadata = MetaData(engine)
  tbl = Table(table_name, metadata, autoload=True)
  mapper(TempTable, tbl)

  # Create a session
  Session = sessionmaker(bind=engine)
  session = Session()

  # Create a fake query and translate
  orm_query = session.query(TempTable)
  translated_query = apply_odata_query(orm_query, odata_query)
  
  # Extract full statement
  statement = str(translated_query.statement.compile(
    dialect=sqlite.dialect(),
    compile_kwargs={"literal_binds": True}))
  
  # Cleanup
  session.close()

  return statement


# Validator: NotEqualTo
class NotEqualTo:
  """
  Validates if the values of two fields are not equal.
  :param fieldname:
      The name of the other field to compare to.
  :param message:
      Error message to raise in case of a validation error. Can be
      interpolated with `%(other_label)s` and `%(other_name)s` to provide a
      more helpful error.
  """

  def __init__(self, fieldname, message=None):
    self.fieldname = fieldname
    self.message = message

  def __call__(self, form, field):
    try:
      other = form[self.fieldname]
    except KeyError:
      raise ValidationError(
        field.gettext("Invalid field name '%s'.") % self.fieldname
      )
    if field.data == other.data:
      d = {
        "other_label": hasattr(other, "label")
        and other.label.text
        or self.fieldname,
        "other_name": self.fieldname,
      }
      message = self.message
      if message is None:
        message = field.gettext("Field must not be equal \
        to %(other_name)s.")

      raise ValidationError(message % d)

# Function to parse OData filters
def parse_odata_filter(query, joins, curr_db_table):
  # Replace ID columns
  query = re.sub('^Id', f'{curr_db_table}.Id', query)
  # Replace lookup column with the associated table
  main_col_matches = re.findall('\w+\/', query)
  main_col_replacements = []
  for match in main_col_matches:
    main_col_replacements.append(joins[match[:-1]]['table'])
  for match, replacement in zip(main_col_matches, main_col_replacements):
    query = re.sub(match, replacement + '.', query)
  
  # Replace slashes with dots
  # query = query.replace('/', '.')
  # lt
  query = query.replace(' lt ', ' < ')
  # le
  query = query.replace(' le ', ' <= ')
  # gt
  query = query.replace(' gt ', ' > ')
  # ge
  query = query.replace(' ge ', ' >= ')
  # eq
  query = query.replace(' eq ', ' = ')
  # ne
  query = query.replace(' ne ', ' != ')
  # startswith(column, string)
  query = re.sub('startsWith', 'startswith', query, re.IGNORECASE)
  matches_sw = re.findall('startswith\(.*?\)', query)
  if len(matches_sw) > 0:
    for match in matches_sw:
      # Extract text between brackets
      sw_terms = re.sub('.*\(', '', match)
      sw_terms = re.sub('\).*', '', sw_terms)
      sw_terms = [s.strip() for s in sw_terms.split(',')]
      sw_terms[1] = re.sub('[^a-zA-Z0-9]', '', sw_terms[1])
      query = re.sub(match.replace('(', '\(').replace(')', '\)'), f"{sw_terms[0]} LIKE '{sw_terms[1]}%'", query)
      
  # substringof(string, column)
  matches_so = re.findall('substringof\(.*?\)', query, re.IGNORECASE)
  if len(matches_so) > 0:
    for match in matches_so:
      # Extract text between brackets
      so_terms = re.sub('.*\(', '', match)
      so_terms = re.sub('\).*', '', so_terms)
      so_terms = [s.strip() for s in so_terms.split(',')]
      so_terms[0] = re.sub('[^a-zA-Z0-9]', '', so_terms[0])
      query = re.sub(match.replace('(', '\(').replace(')', '\)'), f"{so_terms[1]} LIKE '%{so_terms[0]}%'", query)
  
  # day()

  # month()
  
  # year()
  
  # hour()
  
  # minute()
  
  # second()

  return query


# Function to parse OData query
def parse_odata_query(query):
  output = {
    'main_cols': [],
    'join_cols': [],
    'filter_query': '',
    'expand_cols': []
  }
  if not query:
    return output
  for query, value in query.items():
    if query == '$filter':
      output['filter_query'] = value
    else:
      columns = [v.strip() for v in value.split(',')]
      if query == '$select':    
        for column in columns:
          if '/' in column:
            output['join_cols'].append(column)
          else:
            output['main_cols'].append(column)
      elif query == '$expand':
        output['expand_cols'].extend(columns)
  return output

# Function to validate create/update query
conn_string = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
def validate_create_update_query(headers, data, list_id, update=False, item_id=None):
  # 1. Check headers
  xRequestDigest = headers.get('X-RequestDigest')
  if xRequestDigest is None:
    return { 'BadRequest': f"No token provided. Unable to 'authenticate' request." }
  if update:
    # Check IF-MATCH
    ifMatch = headers.get('IF-MATCH')
    if ifMatch is None or ifMatch != '*':
      return { 'BadRequest': f"Incorrect value for IF-MATCH header." }
    # Check X-HTTP-METHOD
    xHttpMethod = headers.get('X-HTTP-METHOD')
    if xHttpMethod is None or xHttpMethod != 'MERGE':
      return { 'BadRequest': f"Incorrect value for X-HTTP-METHOD header." }
  
  # 2. Check for metadata
  metadata = data.get('__metadata')
  if metadata is None:
    return { 'BadRequest': 'Missing JSON item: `__metadata`' }

  # 3. Check ListItemEntityTypeFullName (LIETFN)
  # Check if list exists
  with sqlite3.connect(conn_string) as conn:
    all_tables = get_all_table_names(conn)
  if list_id not in all_tables.id.tolist():
    return { 'BadRequest': 'List does not exist.' }
  # Get metadata
  table = all_tables \
      .rename(columns={'id': 'Id'}) \
      .loc[all_tables.id.eq(list_id)].to_dict('records')[0]
  table_pascal = table['table_db_name'].title().replace('_', '')
  lietfn = f'SP.Data.{table_pascal}ListItem'
  # Retrieve metadata from request
  request_lietfn = metadata.get('type')
  if request_lietfn is None:
    return { 'BadRequest': 'Missing ListItemEntityTypeFullName.' }
  if request_lietfn != lietfn:
    return { 'BadRequest': 'Incorrect ListItemEntityTypeFullName.' }

  # Check if item exists
  with sqlite3.connect(conn_string) as conn:
    df = pd.read_sql(f"SELECT * FROM {table['table_db_name']}", conn)
  if update and int(item_id) not in df.Id.values:
    return { 'BadRequest': 'Item does not exist.' }
  
  return { 
    'Success': True,
    'table': table['table_db_name'],
    'data': df
  }

def validate_delete_query(headers, list_id, item_id=None):
  # 1. Check headers
  xRequestDigest = headers.get('X-RequestDigest')
  if xRequestDigest is None:
    return { 'BadRequest': f"No token provided. Unable to 'authenticate' request." }
  
  # Check IF-MATCH
  ifMatch = headers.get('IF-MATCH')
  if ifMatch is None or ifMatch != '*':
    return { 'BadRequest': f"Incorrect value for IF-MATCH header." }
  # Check X-HTTP-METHOD
  xHttpMethod = headers.get('X-HTTP-METHOD')
  if xHttpMethod is None or xHttpMethod != 'DELETE':
    return { 'BadRequest': f"Incorrect value for X-HTTP-METHOD header." }

  # 3. Check ListItemEntityTypeFullName (LIETFN)
  # Check if list exists
  with sqlite3.connect(conn_string) as conn:
    all_tables = get_all_table_names(conn)
  if list_id not in all_tables.id.tolist():
    return { 'BadRequest': 'List does not exist.' }
  # Get metadata
  table = all_tables \
      .rename(columns={'id': 'Id'}) \
      .loc[all_tables.id.eq(list_id)].to_dict('records')[0]

  # Check if item exists
  with sqlite3.connect(conn_string) as conn:
    df = pd.read_sql(f"SELECT * FROM {table['table_db_name']}", conn)
  if int(item_id) not in df.Id.values:
    return { 'BadRequest': 'Item does not exist.' }
  
  return { 
    'Success': True,
    'table': table['table_db_name'],
    'data': df
  }

def validate_create_update_query_listname(headers, data, list_name, update=False, item_id=None):
  # 1. Check headers
  xRequestDigest = headers.get('X-RequestDigest')
  if xRequestDigest is None:
    return { 'BadRequest': f"No token provided. Unable to 'authenticate' request." }
  if update:
    # Check IF-MATCH
    ifMatch = headers.get('IF-MATCH')
    if ifMatch is None or ifMatch != '*':
      return { 'BadRequest': f"Incorrect value for IF-MATCH header." }
    # Check X-HTTP-METHOD
    xHttpMethod = headers.get('X-HTTP-METHOD')
    if xHttpMethod is None or xHttpMethod != 'MERGE':
      return { 'BadRequest': f"Incorrect value for X-HTTP-METHOD header." }
  
  # 2. Check for metadata
  metadata = data.get('__metadata')
  if metadata is None:
    return { 'BadRequest': 'Missing JSON item: `__metadata`' }

  # 3. Check ListItemEntityTypeFullName (LIETFN)
  # Check if list exists
  with sqlite3.connect(conn_string) as conn:
    all_tables = get_all_table_names(conn)
  if list_name not in all_tables.table_name.tolist():
    return { 'BadRequest': 'List does not exist.' }
  # Get metadata
  table = all_tables \
      .rename(columns={'id': 'Id'}) \
      .loc[all_tables.table_name.eq(list_name)].to_dict('records')[0]
  table_pascal = table['table_db_name'].title().replace('_', '')
  lietfn = f'SP.Data.{table_pascal}ListItem'
  # Retrieve metadata from request
  request_lietfn = metadata.get('type')
  if request_lietfn is None:
    return { 'BadRequest': 'Missing ListItemEntityTypeFullName.' }
  if request_lietfn != lietfn:
    return { 'BadRequest': 'Incorrect ListItemEntityTypeFullName.' }

  # Check if item exists
  with sqlite3.connect(conn_string) as conn:
    df = pd.read_sql(f"SELECT * FROM {table['table_db_name']}", conn)
  if update and int(item_id) not in df.Id.values:
    return { 'BadRequest': 'Item does not exist.' }
  
  return { 
    'Success': True,
    'table': table['table_db_name'],
    'data': df
  }

def validate_delete_query_listname(headers, list_name, item_id=None):

  # 1. Check headers
  xRequestDigest = headers.get('X-RequestDigest')
  if xRequestDigest is None:
    return { 'BadRequest': f"No token provided. Unable to 'authenticate' request." }
  
  # Check IF-MATCH
  ifMatch = headers.get('IF-MATCH')
  if ifMatch is None or ifMatch != '*':
    return { 'BadRequest': f"Incorrect value for IF-MATCH header." }
  # Check X-HTTP-METHOD
  xHttpMethod = headers.get('X-HTTP-METHOD')
  if xHttpMethod is None or xHttpMethod != 'DELETE':
    return { 'BadRequest': f"Incorrect value for X-HTTP-METHOD header." }

  # 3. Check ListItemEntityTypeFullName (LIETFN)
  # Check if list exists
  with sqlite3.connect(conn_string) as conn:
    all_tables = get_all_table_names(conn)
  if list_name not in all_tables.table_name.tolist():
    return { 'BadRequest': 'List does not exist.' }
  # Get metadata
  table = all_tables \
      .rename(columns={'id': 'Id'}) \
      .loc[all_tables.table_name.eq(list_name)].to_dict('records')[0]

  # Check if item exists
  with sqlite3.connect(conn_string) as conn:
    df = pd.read_sql(f"SELECT * FROM {table['table_db_name']}", conn)
  if int(item_id) not in df.Id.values:
    return { 'BadRequest': 'Item does not exist.' }
  
  return { 
    'Success': True,
    'table': table['table_db_name'],
    'data': df
  }

  