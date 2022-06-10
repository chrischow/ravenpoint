# RavenPoint
A SharePoint REST API clone based in Python (Flask) for testing apps that use SharePoint Lists as a backend for storing data.

## Motivation
It's difficult getting access to a S

## Features

### REST API
- Mimics SharePoint's (SP) REST API
- URL parameters:
  - `$select`: For selecting columns from tables
  - `$filter`: For filtering rows by criteria
  - `$expand`: For selecting columns in linked lookup tables


### Admin Dashboard
- Upload a CSV file + dataset name to be stored in a SQLite database
- Check what datasets there are in the database
- Inspect dataset metadata
- Delete datasets

## Installation
Use the `requirements.txt` to create a Conda environment.

## Usage
Navigate to the `ravenpoint` folder, then set up the DB:

```bash
cd ravenpoint

flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

Start the Flask development server:

```bash
python app.py
```

## Resources
- Parser for OData filters: [`odata-query`](https://github.com/gorilla-co/odata-query)

