from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from wtforms import StringField, SubmitField, FileField
from wtforms.validators import DataRequired

class UploadData(FlaskForm):
    csv_file = FileField('Data (CSV file)', [FileAllowed(['csv'], 'CSV files only.')])
    table_name = StringField('Table Name',[DataRequired()])
    
    submit = SubmitField('Upload Data')