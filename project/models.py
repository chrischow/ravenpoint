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