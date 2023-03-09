import sqlite3
from flask_wtf import FlaskForm
from flask_wtf.file import  FileAllowed
from project import app, db
from wtforms import StringField, SubmitField, FileField, BooleanField, SelectField
from wtforms.validators import DataRequired, InputRequired

class UploadData(FlaskForm):
    csv_file = FileField('Data (CSV file)', [FileAllowed(['csv'], 'CSV files only.')])
    table_name = StringField('Table Name', [DataRequired()])
    
    submit = SubmitField('Submit')


class UploadFile(FlaskForm):
    file = FileField('File')
    submit = SubmitField('Submit')

class EditRelationship(FlaskForm):
    table_left = SelectField('Table Name', validators=[InputRequired()], validate_choice=False)
    table_left_on = SelectField('Table Column', validators=[InputRequired()], validate_choice=False)
    table_lookup = SelectField('Lookup Table', validators=[InputRequired()], validate_choice=False)
    
    is_multi = BooleanField('This is a Multi-Lookup Column')
    description = StringField('Description')

    submit = SubmitField('Submit')
