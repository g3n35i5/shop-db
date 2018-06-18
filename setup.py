#!/usr/bin/env python3

import os.path
import sys
import sqlite3
from project.configuration import BaseConfig
from project.cli.utils import choice


if __name__ == '__main__':
    print('Setting up shop.db\n')

    # Check if a database already exists
    if os.path.isfile(BaseConfig.DATABASE_URI):
        sys.exit('Error: A database already exists in the current ' \
                 'directory! Aborting.')

    # Check dependencies
    try:
        import flask
        import flask_bcrypt
        import jwt
        import flask_cors
        import werkzeug
    except ModuleNotFoundError:
        sys.exit('Error: Please read the installation instructions' \
                 'and install the dependencies.')

    try:
        if flask.__version__ != '0.12.2':
            sys.exit('Flask version does not match.')
        if flask_bcrypt.__version__ != '0.7.1':
            sys.exit('flask_bcrypt version does not match.')
        if jwt.__version__ != '1.5.3':
            sys.exit('pyjwt version does not match.')
        if flask_cors.__version__ != '3.0.3':
            sys.exit('flask_cors version does not match.')
        if werkzeug.__version__ != '0.14.1':
            sys.exit('werkzeug version does not match.')
    except:
        sys.exit('The dependency versions could not be checked.')

    print('\t- All dependencies are installed correctly.\n')

    # Setup database
    try:
        with open(BaseConfig.DATABASE_SCHEMA) as models:
            print('\t- Creating database.\n')
            con = sqlite3.connect(BaseConfig.DATABASE_URI)

            schema = models.read()
            print('\t- Reading database scheme.\n')

            con.executescript(schema)
            print('\t- Writing database scheme.\n')

            con.close()
            print('\t- Saving database.\n')
    except:
        sys.exit('Error: Could not create database.')

    print('Success! To get started, please use the manager script to')
    print('add consumers and other objects to the database:')
    print('')
    print('\t./manager.py add {consumer, product, department, ...}')
