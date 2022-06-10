# Create fake data and add to database
import lorem
import numpy as np
import pandas as pd
import sqlite3

from hashlib import md5
from werkzeug.utils import secure_filename

# Configure connection string
conn_string = '/home/chrischow/repos/ravenpoint/project/data/data.sqlite'

# Choices
data_domains = ['Ops', 'Manpower', 'Training', 'Intel', 'Engineering', 'Safety']
frequencies = ['daily', 'weekly', 'monthly', 'quarterly']
dataTypes = ['string', 'integer', 'float', 'boolean', 'datetime']

def get_random_item(choices):
  return choices[int(np.random.choice(list(range(len(choices))), 1))]

# Initialise lists
datasets = []
tables = []
columns = []
business_terms = []

# Create business glossary table
words = set(lorem.paragraph().replace('.', '').lower().split(' '))
words.update(set(lorem.paragraph().replace('.', '').lower().split(' ')))
words = list(words)
definitions = [lorem.sentence() for _ in words]

for i, (word, definition) in enumerate(zip(words, definitions)):
  business_terms.append({
    'termId': i+1,
    'term': word.title(),
    'definition': definition,
    'businessRules': f"{word.title()} business rules",
    'source': 'Raven dictionary'
  })

# Create datasets table
for dataset_i in range(10):
  # Set datasets data
  datasetTitle = f"Dataset {dataset_i+1}"
  useCases = lorem.sentence()
  owner = f"Branch {(dataset_i % 3) + 1}"
  pointOfContact = f"{owner} Staff {(dataset_i % 4) + 1}"
  dataDomain = get_random_item(data_domains)
  datasets.append({
    'datasetTitle': datasetTitle,
    'useCases': useCases,
    'owner': owner,
    'pointOfContact': pointOfContact,
    'dataDomain': dataDomain
  })

  # Create tables table
  for table_i in range(3):
    tableTitle = f"{datasetTitle} Table {table_i+1}"
    tableDescription = lorem.sentence()
    updateFrequency = get_random_item(frequencies)
    parentDatasetID = dataset_i
    site = f"/raven/prototyping"

    hashed_table = md5(tableTitle.encode())
    guid = hashed_table.hexdigest()
    tables.append({
      'tableTitle': tableTitle,
      'tableDescription': tableDescription,
      'updateFrequency': updateFrequency,
      'parentDatasetID': parentDatasetID,
      'site': site,
      'guid': guid
    })

    for col_i in range(10):
      columnTitle = f"{tableTitle} column {col_i+1}"
      columnDescription = lorem.sentence()
      dataType = get_random_item(dataTypes)
      businessRules = f"{columnTitle} business rules"
      parentTableID = table_i
      isPrimaryKey = True if col_i == 1 else False
      isForeignKey = False
      codeTable = ''
      relatedFactTable = ''
      businessTermID = get_random_item(business_terms)['termId']
      columns.append({
        'columnTitle': columnTitle,
        'columnDescription': columnDescription,
        'dataType': dataType,
        'businessRules': businessRules,
        'parentTableID': parentTableID,
        'isPrimaryKey': isPrimaryKey,
        'isForeignKey': isForeignKey,
        'codeTable': codeTable,
        'relatedFactTable': relatedFactTable,
        'businessTermID': businessTermID
      })

# Add to database
table_names = ['DC Datasets', 'DC Tables',
               'DC Columns', 'DC Business Terms']
entity_types = ['dataset', 'table', 'column', 'term']

with sqlite3.connect(conn_string) as conn:
  try:
    for tablename, entity, table in zip(table_names, entity_types, [datasets, tables, columns, business_terms]):
      # Create table
      print(tablename)
      table_db_name = secure_filename(tablename).lower()
      temp_df = pd.DataFrame(table)
      if entity != 'term':
        temp_df = temp_df.reset_index().rename(columns={'index': f'{entity}Id'})
      temp_df.to_sql(
        table_db_name, con=conn, if_exists='replace', index=False,
        dtype={f'{entity}Id': 'INTEGER PRIMARY KEY'}
      )

      # Add to register
      # cursor = conn.cursor()
      # table_hash_id = md5(tablename.encode()).hexdigest()
      # cursor.execute(f"INSERT INTO tables (id, table_name, table_db_name) \
      #   VALUES ('{table_hash_id}', '{tablename}', '{table_db_name}')")
  except Exception as e:
    print(e)
    conn.rollback()
  