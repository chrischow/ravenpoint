import os
import pandas as pd
import sqlite3

from flask import render_template, Blueprint, url_for, redirect, request, flash, send_from_directory
from project import db, app
from project.admin.forms import UploadData
from project.models import Table
from project.utils import get_all_table_names, translate_odata
from werkzeug.utils import secure_filename

admin = Blueprint(
    'admin', __name__,
    template_folder='templates'
)

@admin.route('/', methods=['GET', 'POST'])
def index():
    # Test
    qry = translate_odata(app.config['SQLALCHEMY_DATABASE_URI'], 'mock_data',
                          "(first_name eq 'John') and (score le 0)")
    print(qry)

    # Handle password changes
    form = UploadData()

    # Connect to database
    conn = sqlite3.connect(
        app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    )

    all_tables = get_all_table_names(conn)
    nrows = []
    all_columns = []
    for table_name in all_tables.table_db_name:
        # Get columns
        cursor = conn.execute(f"SELECT * FROM {table_name}")
        columns = ', '.join(list(map(lambda x: x[0], cursor.description)))
        all_columns.append(columns)

        # Get no. of rows
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        table_nrows = cursor.fetchone()[0]
        nrows.append(table_nrows)

    all_tables['nrows'] = nrows
    all_tables['columns'] = all_columns

    conn.close()
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
            if 'id' not in df.columns:
                flash("<code>id</code> column not found.", 'danger')
                return redirect(url_for('admin.index'))
            
            table_name = form.table_name.data
            table_db_name = secure_filename(form.table_name.data).lower()

            # Load into sqlite
            try:
                # Add table to database
                conn = sqlite3.connect(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
                df.to_sql(table_db_name, con=conn, if_exists='replace', index=False,
                          dtype={'id': 'INTEGER PRIMARY KEY'})
                conn.close()

                # Add table to register
                new_table = Table(table_name, table_db_name)
                db.session.add(new_table)
                db.session.commit()

            except Exception as e:
                print('Error loading data into database:')
                print(e)

                flash(f"Failed to load data into database:\n{e}", 'danger')
                return redirect(url_for('admin.index'))

            # Message
            flash(f'Successfully loaded data into database as {table_name}.', 'success')
            return redirect(url_for('admin.index'))
    
        else:
            print(form.errors)
            for field, error_msg in form.errors.items():
                flash(f'Form submission failed: {" ".join(error_msg)}', 'danger')

    return render_template('index.html', form=form, tables=all_tables.to_dict('records'))


@admin.route('/table/<string:table_name>', methods=['GET'])
def table_view(table_name):
    # Connect to database
    conn = sqlite3.connect(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))

    # Check if table is valid - redirect back to admin panel if not
    all_tables = get_all_table_names(conn)
    if table_name not in all_tables.name.tolist():
        flash('Invalid table.')
        return redirect(url_for('admin.index'))
    
    # Get data
    df = pd.read_sql(f'SELECT * FROM {table_name}', conn)
    conn.close()
    
    return render_template('table.html', table=df.to_dict('records'),
                            columns=df.columns.tolist(), table_name=table_name)
    

