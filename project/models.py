from hashlib import md5
from project import db

class Table(db.Model):
  __tablename__ = 'tables'
  id = db.Column(db.String(128), primary_key=True)
  table_name = db.Column(db.String(256), unique=True, index=True)
  table_db_name = db.Column(db.String(256))

  def __init__(self, table_name, table_db_name):
    hashed = md5(table_name.encode())
    self.id = hashed.hexdigest()
    self.table_name = table_name
    self.table_db_name = table_db_name

    def get_id(self):
      return self.user_id

class Relationship(db.Model):
  __tablename__ = 'relationships'
  rship_id = db.Column(db.Integer, primary_key=True)
  table_left = db.Column(db.String(128))
  table_left_on = db.Column(db.String(128))
  table_lookup = db.Column(db.String(128))
  table_lookup_on = db.Column(db.String(128))
  description = db.Column(db.String(255))

  def __init__(self, table_left, table_left_on, table_lookup, table_lookup_on, description=''):
    self.table_left = table_left
    self.table_left_on = table_left_on
    self.table_lookup = table_lookup
    self.table_lookup_on = table_lookup_on
    self.description = description