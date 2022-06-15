import sqlite3
from flask_wtf import FlaskForm
from flask_wtf.file import  FileAllowed
from project import app, db
from project.utils import NotEqualTo
from wtforms import StringField, SubmitField, FileField, BooleanField
from wtforms.validators import DataRequired

class UploadData(FlaskForm):
    csv_file = FileField('Data (CSV file)', [FileAllowed(['csv'], 'CSV files only.')])
    table_name = StringField('Table Name', [DataRequired()])
    
    submit = SubmitField('Submit')

class EditRelationship(FlaskForm):
    table_left = StringField('Table Name', [DataRequired(), NotEqualTo('table_lookup')])
    table_left_on = StringField('Table Column', [DataRequired()])
    table_lookup = StringField('Lookup Table', [DataRequired()])
    table_lookup_on = StringField('Lookup Table Column', [DataRequired()])
    is_multi = BooleanField('This is a Multi-Lookup Column')
    description = StringField('Description')

    submit = SubmitField('Submit')
