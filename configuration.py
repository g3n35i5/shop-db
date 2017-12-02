#!/usr/bin/env python3
'''
This file contains the backend configuration for flask and shop-db itself
'''

import app


class BaseConfig(object):
    SECRET_KEY = 'supersecretkey'
    DEBUG = False
    TEST = False
    DATABASE_URI = app.PATH + '/shop.db'
    DATABASE_SCHEMA = app.PATH + '/models.sql'
    HOST = '0.0.0.0'
    PORT = 5000

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TEST = True

class UnittestConfig(DevelopmentConfig):
    DATABASE_URI = ':memory:'
