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
  return pd.DataFrame(df)

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