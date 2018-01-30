#!/usr/bin/env python3
'''
This file contains the backend configuration for flask and shop-db itself
'''
import os.path

class BaseConfig(object):
    SECRET_KEY = 'supersecretkey'
    __path = os.path.dirname(__file__)
    DEBUG = True
    TEST = True
    DATABASE_URI = __path + '/shop.db'
    DATABASE_SCHEMA = __path + '/models.sql'
    HOST = '0.0.0.0'
    PORT = 5000
    USE_KARMA = True

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TEST = True

class UnittestConfig(DevelopmentConfig):
    DATABASE_URI = ':memory:'
