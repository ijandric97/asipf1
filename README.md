# ASIP F1

## Overview

Formula 1 data correlation analysis project for the "Systems and Data Analysis" course at the University of Rijeka, Faculty of Engineering

## Database image file

The f1db.sqlite is an SQLite converted ErgastDb dump downloaded from http://ergast.com/mrd/db/ which was last updated on: 2023-01-07.
The original MySQL dump is loaded using phpMyAdmin to MySQL and then exported to SQLite using the following python package: https://pypi.org/project/mysql-to-sqlite3/

## How to run
This code has only been tested on Python 3.11.

First create a virtual environment and activate it.
```bash
$ python -m venv venv
$ source venv\bin\activate
```

Install poetry dependency manager and then dependencies using it.
```bash
pip install poetry
poetry install
```

Run the program
```
python ./asipf1/__init__.py
```

## Results
The generated CSV files can be found in the data folder.
The generated image plots can be found in the images folder.
