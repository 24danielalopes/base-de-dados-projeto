# base-de-dados-projeto

A database-driven web application built for the **Bases de Dados** (Databases) course. The project involves organizing a dataset into a relational SQL database, accessing it with Python, and presenting the data through HTML pages.

## Overview

The dataset was provided by the course instructors. As part of the project, I:

- Designed and organized the data into a relational database using SQL
- Wrote Python code to connect to the database and run queries
- Built HTML pages to display the data to the user

## Technologies

- **SQL** (SQLite)
- **Python 3** (Flask)
- **HTML**

## Project Structure

- `contratos_publicos.sql` - SQL script to create the database schema and insert the data
- `db.py` - database connection and queries
- `app.py` - Flask application (routes and page logic)
- `server.py` - entry point that starts the web server
- `templates/` - HTML pages
- `static/` - static files (CSS, images)

## How to Run

1. Create the database from the SQL script:

       sqlite3 contratos_publicos.db < contratos_publicos.sql

2. Install the dependencies:

       pip install flask

3. Start the server:

       python3 server.py

4. Open http://localhost:8080 in your browser.

## Notes

The original dataset was provided by the course instructors. The database can be recreated from the SQL file included in this repository.
