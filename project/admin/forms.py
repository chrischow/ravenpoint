import sqlite3
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from project import app, db
from project.utils import NotEqualTo
from wtforms import StringField, SubmitField, FileField
from wtforms.validators import DataRequired

class UploadData(FlaskForm):
    csv_file = FileField('Data (CSV file)', [FileAllowed(['csv'], 'CSV files only.')])
    table_name = StringField('Table Name', [DataRequired()])
    
    submit = SubmitField('Submit')

class EditRelationship(FlaskForm):
    table_left = StringField('Table 1 Name', [DataRequired(), NotEqualTo('table_right')])
    table_left_on = StringField('Table 1 Column', [DataRequired()])
    table_right = StringField('Table 2 Name', [DataRequired()])
    table_right_on = StringField('Table 2 Column', [DataRequired()])
    description = StringField('Description')

    submit = SubmitField('Submit')
