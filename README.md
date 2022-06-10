# RavenPoint
A SharePoint REST API clone based in Python (Flask) for testing apps that use SharePoint Lists as a backend for storing data.

## Motivation
There is a huge disparity between the development and production environments for Team Raven's React.js apps. This creates a challenge in developing the frontend and the backend for the apps at the same time - something that ought to be done when using React.js. Specifically, the development of the frontend and some of the backend features happens in the development environment, and all interaction with databases happens in sandboxes in the production environment. of code to query SharePoint (SP) List data via the SP OData REST API.

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
First, clone this repository to a local directory.

Second, use the `requirements.txt` file to install the dependencies in a virtual environment.

Third, navigate to the `ravenpoint` folder and set up the DB:

```bash
cd ravenpoint

flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Usage
In the `ravenpoint` folder, start the Flask development server:

```bash
cd ravenpoint
python app.py
```

## Resources
- Parser for OData filters: [`odata-query`](https://github.com/gorilla-co/odata-query)

