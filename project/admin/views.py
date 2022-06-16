import json
import os
from traceback import format_exception_only
import pandas as pd
import sqlite3

from flask import render_template, Blueprint, url_for, redirect, request, flash, send_from_directory
from project import db, app
from project.admin.forms import UploadData, EditRelationship
from project.models import Table, Relationship
from project.utils import get_all_table_names, get_all_table_metadata, translate_odata, \
    get_all_relationships
from werkzeug.utils import secure_filename

admin = Blueprint(
    'admin', __name__,
    template_folder='templates'
)

# Configure connection string
conn_string = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')

@admin.route('/', methods=['GET', 'POST'])
def index():
    # Test
    # qry = translate_odata(app.config['SQLALCHEMY_DATABASE_URI'], 'mock_data',
    #                       "(first_name eq 'John') and (score le 0)")
    # print(qry)

    # Initialise form
    form = UploadData()

    # Get tables metadata
    with sqlite3.connect(conn_string) as conn:
        all_tables = get_all_table_names(conn)
        table_metadata = get_all_table_metadata(conn, all_tables)

    if request.method == 'POST':
        if form.validate_on_submit():
            
            # Upload file to server
            upload_dir = app.config['UPLOAD_FOLDER']
            csv_file = request.files['csv_file']
            filename = secure_filename(csv_file.filename)
            filepath = os.path.join(upload_dir, filename)
            csv_file.save(filepath)
            
            # Read data and cleanup
            df = pd.read_csv(filepath)
            os.remove(filepath)

            # Check that data includes `id` column
            if 'Id' in df.columns:
                df = df.rename(columns={'Id': 'Old_Id'})
                df = df.reset_index().rename(columns={'index': 'Id'})
            
            table_name = form.table_name.data
            table_db_name = secure_filename(form.table_name.data).lower()

            # Load into sqlite
            try:
                # Add table to database
                with sqlite3.connect(conn_string) as conn:
                    df.to_sql(table_db_name, con=conn, if_exists='replace', index=False,
                            dtype={f'{df.columns[0]}': 'INTEGER PRIMARY KEY'})

                # Add table to register
                new_table = Table(table_name, table_db_name)
                db.session.add(new_table)
                db.session.commit()

            except Exception as e:
                print('Error loading data into database:')
                print(e)
                db.session.rollback()
                flash(f"Failed to load data into database:\n{e}", 'danger')
                return redirect(url_for('admin.index'))

            # Message
            flash(f'Successfully loaded data into database as {table_name}.', 'success')
            return redirect(url_for('admin.index'))
    
        else:
            print(form.errors)
            for field, error_msg in form.errors.items():
                flash(f'Form submission failed: {" ".join(error_msg)}', 'danger')
    
    return render_template('index.html', form=form, tables=table_metadata.to_dict('records'))

# Table view
@admin.route('/table/<string:id>', methods=['GET'])
def table_view(id):
    # Get table
    table = Table.query.filter_by(id=id).first_or_404()
    
    # Connect to database
    with sqlite3.connect(conn_string) as conn:
        # Get data
        df = pd.read_sql(f'SELECT * FROM {table.table_db_name}', conn)
    
    return render_template('table.html', table=df.to_dict('records'), id=id,
                            columns=df.columns.tolist(), table_name=table.table_name,
                            table_db_name=table.table_db_name)

# Delete table endpoint
@admin.route('/table/<string:id>/delete', methods=['POST'])
def table_delete(id):
    # Delete id
    table = Table.query.filter_by(id=id).first_or_404()
    # print(table)
    # Run delete query
    with sqlite3.connect(conn_string) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(f'DROP TABLE {table.table_db_name}')
            cursor.execute(f"DELETE FROM tables WHERE id='{id}'")
            conn.commit()
        except Exception as e:
            conn.rollback()
            flash(f'Error: Could not delete {table.table_db_name}. \n{e}', 'danger')
            return redirect(url_for('admin.table_view', id=id))
    return redirect(url_for('admin.index'))
        

@admin.route('/relationships', methods=['GET', 'POST'])
def relationships():

    # Initialise form
    form = EditRelationship()
    
    # Get all relationships
    with sqlite3.connect(conn_string) as conn:
        all_relationships = get_all_relationships(conn)
    if request.method == 'POST':
        if form.validate_on_submit():
            # Extract form data
            table_left = form.table_left.data
            table_left_on = form.table_left_on.data
            table_lookup = form.table_lookup.data
            table_lookup_on = 'Id'
            is_multi = form.is_multi.data
            description = form.description.data

            # Create new relationship
            new_rship = Relationship(table_left, table_left_on, table_lookup, 
                                     table_lookup_on, is_multi, description)

            # Create new junction table
            if is_multi:
                # Get left table
                with sqlite3.connect(conn_string) as conn:
                    df = pd.read_sql(F'SELECT * FROM {table_left}', con=conn)
                
                    # Transform lookup table into a junction table
                    df[table_left_on] = df[table_left_on].str.split(',')
                    df = df[['Id', table_left_on]].explode(table_left_on)
                    
                    # Clean data format and index and column names
                    df[table_left_on] = pd.to_numeric(df[table_left_on])
                    df = df.dropna()
                    df[table_left_on] = df[table_left_on].astype(int)
                    df = df.reset_index(drop=True).reset_index()
                    df = df.rename(columns={'Id': f'{table_left}_pk', table_left_on: f'{table_lookup}_pk', 'index': 'Id'})

                    # Save to database
                    df.to_sql(f'{table_left}_{table_lookup}', con=conn, if_exists='replace', index=False,
                                dtype={f'{df.columns[0]}': 'INTEGER PRIMARY KEY'})
            
            # Commit changes
            try:
                db.session.add(new_rship)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f"Failed to load data into database:\n{e}", 'danger')
                return redirect(url_for('admin.relationships'))
            
            return redirect(url_for('admin.relationships'))
        else:
            # Print errors
            for field, error_msg in form.errors.items():
                for err in error_msg:
                    print(f"{field}:  {err}")
    return render_template('relationships.html', form=form,
                           relationships=all_relationships.to_dict('records'))

@admin.route('/relationship/<int:id>', methods=['GET', 'POST'])
def relationship(id):

    # Initialise form
    form = EditRelationship()

    # Retrieve item
    rship = Relationship.query.get(id)
    output = {
        'table_left': rship.table_left,
        'table_left_on': rship.table_left_on,
        'table_lookup': rship.table_lookup,
        'is_multi': rship.is_multi,
        'description': rship.description
    }

    if request.method == 'GET':
        form.table_left.data = rship.table_left
        form.table_left_on.data = rship.table_left_on
        form.table_lookup.data = rship.table_lookup
        form.is_multi.data = rship.is_multi
        form.description.data = rship.description

    if request.method == 'POST' and form.validate_on_submit():
        # Extract form data
        rship.table_left = form.table_left.data
        rship.table_left_on = form.table_left_on.data
        rship.table_lookup = form.table_lookup.data
        rship.table_lookup_on = 'Id'
        rship.is_multi = form.is_multi.data
        rship.description = form.description.data
        db.session.commit()
        return redirect(url_for('admin.relationships'))

    return render_template('relationship.html', form=form, id=id, rship=json.dumps(output))

@admin.route('/relationship/<int:id>/delete', methods=['POST'])
def relationship_delete(id):
    # Delete id
    rship = Relationship.query.get(id)
        
    # Run delete query
    try:
            
        if rship.is_multi:
            db.session.execute(f'DROP TABLE {rship.table_left}_{rship.table_lookup}')
        db.session.delete(rship)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error: Could not delete relationship ID={rship.rship_id}. \n{e}', 'danger')
        return redirect(url_for('admin.relationships'))
    return redirect(url_for('admin.relationships'))

@admin.route('/guide', methods=['GET'])
def guide():
    return render_template('guide.html')


@admin.route('/get_tables', methods=['GET'])
def get_tables():
    with sqlite3.connect(conn_string) as conn:
        all_tables = get_all_table_names(conn)
        table_metadata = get_all_table_metadata(conn, all_tables)
        table_metadata['columns'] = table_metadata['columns'].str.replace(' ', '', regex=False)
    
    return {'data': table_metadata.to_dict('records')}