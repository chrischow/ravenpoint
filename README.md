# RavenPoint
A SharePoint REST API clone built in Python (Flask) for testing apps that use SharePoint Lists as a backend for storing data.

## Motivation
There is a huge disparity between the development and production environments for Team Raven's React.js apps due to ******* ******** IT policy. This creates challenges in development.

First, the development of the frontend and some of the backend features happens in the development environment, and development of code to interact with databases happens in sandboxes in the production environment. This surely isn't a best practice for React apps. It isn't possible to test code to query data from SharePoint (SP) Lists via the SP OData REST API.

Second, this affects the build process. Apps cannot be bundled into a production build, since development still happens after code is ported over into the production environment. That means the whole universe of awesome open-source React components that cannot be bundled into individual JS files are off limits.

## Value Proposition

### Near-to-Medium Term
RavenPoint aims to enable Team Raven to do all development in a single environment (i.e. not on internal servers). Instead of trying to bring modern development tools in, which will probably never happen in the next few generations, we aim to emulate the internal stack on the outside.

If all development and testing can happen on the outside, we can (1) make full use of open-source tech in our apps because we can (2) create production builds without worrying about having to amend the code later on. 

## Features

### REST API
- Mimics SharePoint's (SP) REST API
- URL parameters:
  - `$select`: For selecting columns from tables
  - `$filter`: For filtering rows by criteria
  - `$expand`: For selecting columns in linked lookup tables

### Admin Dashboard
- Upload a CSV file + table name to be stored in a SQLite database
- Check table metadata (ID, title, columns)
- Inspect tables
- Delete tables

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
- Parser for OData filters: [odata-query](https://github.com/gorilla-co/odata-query)

