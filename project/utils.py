# RAVENPOINT UTILITIES
import pandas as pd
import re
import sqlite3


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