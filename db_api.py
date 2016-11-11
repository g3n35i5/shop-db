#!/usr/bin/env python3

import sqlite3
from models import Product

# convert booleans since sqlite3 has no booleans
# see: https://www.sqlite.org/datatype3.html#boolean_datatype
sqlite3.register_adapter(bool, int)
sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))


class DatabaseApiException(Exception):

    def __init__(self, model):
        self.model = model


class ObjectNotFound(DatabaseApiException):

    def __init__(self, model, id):
        self.model = model
        self.id = id

    def __str__(self):
        return '{0.model.__name__} with id={0.id} not found.'.format(self)


def factory(cls):
    """ Helper function for ORM Mapping """
    def fun(cursor, row):
        p = cls()
        for idx, col in enumerate(cursor.description):
            setattr(p, col[0], row[idx])
        return p
    return fun


class DatabaseApi(object):

    def __init__(self, sqlite3_connection):
        self.con = sqlite3_connection
