# RavenPoint
A SharePoint REST API clone built in Python (Flask) for testing apps that use SharePoint Lists as a backend for storing data.

<p>
    <a href="https://www.python.org/">
        <img src="http://ForTheBadge.com/images/badges/made-with-python.svg">
    </a>
    <a href="https://flask.palletsprojects.com/en/2.0.x/">
        <img src="docs/images/bottled-in-flask.svg">
    </a>
</p>

## Motivation
There is a huge disparity between the development and production environments for Team Raven's React.js apps due to ******* ******** IT policy. This creates challenges in development.

First, the development of the frontend and some of the backend features happens in the development environment, and development of code to interact with databases happens in sandboxes in the production environment. This surely isn't a best practice for React apps. It isn't possible to test code to query data from SharePoint (SP) Lists via the SP OData REST API.

Second, this affects the build process. Apps cannot be bundled into a production build, since development still happens after code is ported over into the production environment. That makes it extremely challenging to use awesome open-source React components that cannot be easily bundled into individual JS files.

## Value Proposition
RavenPoint aims to enable Team Raven to do all development in a single environment (i.e. not on internal servers). Instead of trying to bring modern development tools in, which will probably never happen in the next few generations, we aim to emulate the internal stack on the outside.

If all development and testing can happen on the outside, we can (1) make full use of open-source tech in our apps because we can (2) create production builds without worrying about having to amend the code later on. 

In the longer term, when (or if) an internal cloud is made available, RavenPoint can potentially be the bridge between (a) apps that still use dated OData queries and (b) modern databases in the backend - this is exactly how RavenPoint is set up.

## Features

### REST API
- Mimics SharePoint's (SP) REST API
- URL parameters:
  - `$select`: For selecting columns from tables
  - `$filter`: For filtering rows by criteria
  - `$expand`: For selecting columns in linked lookup tables

![](./docs/images/ss_ravenpoint_swagger_ui.jpg)

### Admin Dashboard
- Upload a CSV file + table name to be stored in a SQLite database
- Check table metadata (ID, title, columns)
- Inspect tables
- Delete tables

![](./docs/images/ss_ravenpoint_admin.jpg)

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
- OData query operators: [Microsoft documentation](https://docs.microsoft.com/en-us/sharepoint/dev/sp-add-ins/use-odata-query-operations-in-sharepoint-rest-requests)
- Parser for OData filters: [odata-query](https://github.com/gorilla-co/odata-query)
- NotEqualTo Validator: [wtforms-validators](https://github.com/akhilharihar/wtforms-validators)

## Notes

### Logic for OData Filter Parser
Test queries:

- Starts with:

  ```
  http://127.0.0.1:5000/ravenpoint/_api/web/Lists(guid'797f269d2c37d29d15a19c40ec49bada')/items?$select=Id,tableTitle,parentDatasetID/datasetTitle,parentDatasetID/dataDomain,parentDatasetID/owner&$expand=parentDatasetID&$filter=startswith(parentDatasetID/dataDomain,'O') and startswith(parentDatasetID/owner,'B')
  ```

- Substring of:

  ```
  http://127.0.0.1:5000/ravenpoint/_api/web/Lists(guid'797f269d2c37d29d15a19c40ec49bada')/items?$select=Id,tableTitle,parentDatasetID/datasetTitle,parentDatasetID/dataDomain,parentDatasetID/owner&$expand=parentDatasetID&$filter=substringof('O', parentDatasetID/dataDomain) and substringof('2', parentDatasetID/owner)
  ```

- Multiple expansion:

  ```
  http://127.0.0.1:5000/ravenpoint/_api/web/Lists(guid'c82cc553edae91adc412ab2723541399')/items?$select=Id,columnTitle,parentTableID/tableTitle,parentTableID/updateFrequency,businessTermID/term,businessTermID/source&$expand=parentTableID,businessTermID&$filter=parentTableID/updateFrequency eq 'daily'
  ```

#### Approach 1: Convert to SQL
The idea is to make minimal changes to the OData query to convert it to SQL. Currently, this involves:

1. Converting `lookupColumn/` to `rightTableDbName/`
2. Replacing operators:
  - E.g. ` le ` to ` < `
  - E.g. ` ne ` to ` != `
3. Replacing functions: `startswith` and `substringof`
  1. Extract parameters between the brackets
  2. Re-write them as `Column LIKE string%` and `Column LIKE %string%` respectively

For the date functions `day`, `month`, `year`, `hour`, `minute`, `second`, more work needs to be done. Fortunately, SQLite has some [datetime functions](https://www.sqlite.org/lang_datefunc.html) to work with. Preliminary concept:

1. Convert all `datetime'YYYY-MM-DD-...'` strings to `date('YYYY-MM-DD-...')`
2. Convert all `day/month/year/hour/minute/second([Colname | datetime'YYYY-MM-DD...'])` strings to `strptime([Colname | datetime'YYYY-MM-DD...'], '[%d | %m | %Y | %H | %M | %S]')`