# Create fake data and add to database
import lorem
import numpy as np
import requests
import pandas as pd
import sqlite3

from datetime import datetime, timedelta
from faker import Faker
from hashlib import md5
from tqdm import tqdm
from werkzeug.utils import secure_filename

# Configure connection string
conn_string = '/home/chrischow/repos/ravenpoint/project/data/data.sqlite'

# Set up faker
fake = Faker()

# Lookups
teams = [
  dict(teamName='HQ', slug='hq'),
  dict(teamName='Marketing', slug='marketing'),
  dict(teamName='HR', slug='hr'),
  dict(teamName='Finance', slug='finance'),
  dict(teamName='R&D', slug='research-devt'),
  dict(teamName='IT', slug='it')
]

max_scores = [int(x) for x in range(10, 110, 10)]
frequencies = {
  'annual': [('WY22/23', '2022-04-01', '2023-03-31')],
  'quarterly': [
    ('WY22 Q1', '2022-04-01', '2022-06-30'), ('WY22 Q2', '2022-07-01', '2022-09-30'),
    ('WY22 Q3', '2022-10-01', '2022-12-31'), ('WY22 Q4', '2023-01-01', '2023-03-31')],
  'monthly': [
    ('Apr 22', '2022-04-01', '2022-04-30'), ('May 22', '2022-05-01', '2022-05-31'),
    ('Jun 22', '2022-06-01', '2022-06-30'), ('Jul 22', '2022-07-01', '2022-07-31'),
    ('Aug 22', '2022-08-01', '2022-08-31'), ('Sep 22', '2022-09-01', '2022-09-30'), 
    ('Oct 22', '2022-10-01', '2022-10-31'), ('Nov 22', '2022-11-01', '2022-11-30'),
    ('Dec 22', '2022-12-01', '2022-12-31'), ('Jan 23', '2023-01-01', '2023-01-31'),
    ('Feb 23', '2023-02-01', '2023-02-28'), ('Mar 23', '2023-03-01', '2023-03-31'), 
  ]
}

# Params
NUM_OBJECTIVES = 3
NUM_STAFF = 3
NUM_KR = 3
NUM_UPDATES = 2
objectives = []
key_results = []
updates = []

# Generate objectives
print('Generating objectives...')
for team in teams:
  for freq, dates in frequencies.items():
    for obj_no in range(1, NUM_OBJECTIVES+1):
      for name, startDate, endDate in dates:
        # Add team objective
        if freq != 'monthly':
          obj_title = f"{team['teamName']} {name} O{obj_no}"
          objectives.append({
            'Title': obj_title,
            'objectiveDescription': f"{fake.catch_phrase()} to {fake.bs()}",
            'objectiveStartDate': startDate,
            'objectiveEndDate': endDate,
            'team': team['teamName'],
            'owner': '',
            'frequency': freq
          })
        else:
          for staff_no in range(1, NUM_STAFF+1):
            month = datetime(*[int(num) for num in startDate.split('-')]).strftime('%b')
            obj_title = f"{team['teamName']} Staff {staff_no} {name} O{obj_no}"
            objectives.append({
              'Title': obj_title,
              'objectiveDescription': f"{fake.catch_phrase()} to {fake.bs()}",
              'objectiveStartDate': startDate,
              'objectiveEndDate': endDate,
              'team': team['teamName'],
              'owner': f'Staff {staff_no}',
              'frequency': freq
            })
      
# Convert to dataframe
df_objectives = pd.DataFrame(objectives) \
  .reset_index() \
  .rename(columns={'index': 'Id'})

# Generate KRs
print('Generating key results...')
for i, row in df_objectives.iterrows():
  for kr_no in range(1, NUM_KR + 1):
    kr_title = f"{row.Title} KR {kr_no}"
    random_max = np.random.choice(max_scores)
    random_prob = np.random.random()
    key_results.append({
      'Title': kr_title,
      'krDescription': f"{fake.catch_phrase()} to {fake.bs()}",
      'krStartDate': row.objectiveStartDate,
      'krEndDate': row.objectiveEndDate,
      'minValue': 0,
      'maxValue': random_max,
      'currentValue': random_max if random_prob < 0.2 else int(random_max * random_prob),
      'parentObjective': row.Id
    })

# Convert to dataframe
df_key_results = pd.DataFrame(key_results) \
  .reset_index() \
  .rename(columns={'index': 'Id'})

# Get team lookup
df_team_lookup = df_objectives.set_index('Id').team.to_dict()

# Get objective lookup
df_kr_to_obj = df_key_results.set_index('Id').parentObjective.to_dict()

# Generate updates
print('Generating updates...')
for i, row in df_key_results.iterrows():
  for updateDate in [row.krStartDate, row.krEndDate]:
    updates.append({
      'updateText': fake.catch_phrase(),
      'updateDate': updateDate,
      'parentKrId': int(row.Id),
      'team': df_team_lookup[df_kr_to_obj[row.Id]]
    })

# Convert to dataframe
df_updates = pd.DataFrame(updates) \
  .reset_index() \
  .rename(columns={'index': 'Id'})

# Write to SQLite
# print('Saving to database...')
# table_names = ['ROKR Objectives', 'ROKR Key Results', 'ROKR Updates']
# tables = [df_objectives, df_key_results, df_updates]

# with sqlite3.connect(conn_string) as conn:
#   try:
#     for tablename, table in zip(table_names, tables):
#       # Create table
#       print(tablename)
#       table_db_name = secure_filename(tablename).lower()
#       temp_df = pd.DataFrame(table)
#       temp_df.to_sql(
#         table_db_name, con=conn, if_exists='replace', index=False,
#         dtype={f'Id': 'INTEGER PRIMARY KEY'}
#       )

#       # Add to register
#       cursor = conn.cursor()
#       table_hash_id = md5(tablename.encode()).hexdigest()
#       cursor.execute(f"INSERT OR REPLACE INTO tables (id, table_name, table_db_name) \
#         VALUES ('{table_hash_id}', '{tablename}', '{table_db_name}')")
#   except Exception as e:
#     print(e)
#     conn.rollback()

# Write to JSON
print('Writing to JSON...')
import json

with open('./exports/objectives.json', 'w') as f:
  json.dump({'data': df_objectives.to_dict('records')}, f)

with open('./exports/keyResults.json', 'w') as f:
  json.dump({'data': df_key_results.to_dict('records')}, f)

with open('./exports/updates.json', 'w') as f:
  json.dump({'data': df_updates.to_dict('records')}, f)