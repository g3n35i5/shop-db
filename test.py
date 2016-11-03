#!/usr/bin/env python3

import sqlite3
from db_api import DatabaseApi
from models import Product

con = sqlite3.connect("foo.db", detect_types=sqlite3.PARSE_DECLTYPES)
api = DatabaseApi(con)
print(api.get_products())

try:
    print(api.get_product_by_id(2))
except Exception as e:
    print(e)


p = Product(id=2, name="Hans", price=110)
print(p)

# TODO: should drop error because id is set!

Product(name="Hans")
# TODO: should drop error because items are missing! Defaults?
