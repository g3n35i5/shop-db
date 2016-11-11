#!/usr/bin/env python3

import sqlite3
from models import Consumer, Product, Purchase, Deposit
import pdb
import datetime

# convert booleans since sqlite3 has no booleans
# see: https://www.sqlite.org/datatype3.html#boolean_datatype
sqlite3.register_adapter(bool, int)
sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))


class DatabaseApiException(Exception):
    def __init__(self, model):
        self.model = model


class NonExistentModel(DatabaseApiException):
    def __init__(self, model):
        self.model = model

    def __str__(self):
        return 'non existent Model {0.model.__name__}.'.format(self)


class NonExistentTable(DatabaseApiException):
    def __init__(self, table):
        self.table = table

    def __str__(self):
        return 'non existent table {0.table.__name__}.'.format(self)


class FieldIsNone(DatabaseApiException):
    def __init__(self, model, field):
        self.model = model
        self.field = field

    def __str__(self):
        return '{0.model.__name__}: field {0.field} is None'.format(self)


class ObjectNotFound(DatabaseApiException):
    def __init__(self, table, id, name):
        self.table = table
        self.id = id
        self.name = name

    def __str__(self):
        return '{0.table.__name__} with \
            id={0.id}/name={0.name} not found.'.format(self)


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

    def insert_object(self, object):
        cur = self.con.cursor()
        # Handle products
        if isinstance(object, Product):
            for (i, n) in zip([object.name,
                               object.active,
                               object.on_stock,
                               object.price],
                              ["name",
                               "active",
                               "on_stock",
                               "price"]):
                if i is None:
                    raise FieldIsNone(model=Product, field=n)

            cur.execute(
                'INSERT INTO product (name, active, on_stock, price) '
                'VALUES (?,?,?,?);',
                (object.name, object.active, object.on_stock, object.price)
            )
            self.con.commit()

        # Handle consumer
        elif isinstance(object, Consumer):
            for (i, n) in zip([object.name, object.active, object.credit],
                              ["name", "active", "credit"]):
                if i is None:
                    raise FieldIsNone(model=Product, field=n)

            cur.execute(
                'INSERT INTO consumer (name, active, credit) '
                'VALUES (?,?,?);',
                (object.name, object.active, object.credit)
            )
            self.con.commit()

        # Handle purchase
        elif isinstance(object, Purchase):
            for (i, n) in zip([object.consumer_id,
                               object.product_id,
                               object.revoked,
                               object.timestamp,
                               object.paid_price],
                              ["consumer_id",
                               "product_id",
                               "revoked",
                               "timestamp",
                               "paid_price"]):
                            if i is None:
                                raise FieldIsNone(model=Product, field=n)

            cur.execute(
                'INSERT INTO purchase (consumer_id,\
                product_id,\
                revoked,\
                timestamp,\
                paid_price) '
                'VALUES (?,?,?,?,?);',
                (object.consumer_id,
                 object.product_id,
                 object.revoked,
                 object.timestamp,
                 object.paid_price)
            )
            self.con.commit()

        # Handle deposit
        elif isinstance(object, Deposit):
            for (i, n) in zip([object.consumer_id,
                               object.amount,
                               object.timestamp],
                              ["consumer_id",
                               "amount",
                               "timestamp"]):
                if i is None:
                    raise FieldIsNone(model=Product, field=n)
            cur.execute(
                'INSERT INTO deposit (consumer_id, amount, timestamp) '
                'VALUES (?,?,?);',
                (object.consumer_id, object.amount, object.timestamp))
            self.con.commit()
        else:
            raise NonExistentModel(object)

    def get_one(self, table, id=None, name=None):
        if id is None and name is None:
            raise("get_object: at least one identifier required")
        cur = cur = self.con.cursor()

        if table not in ['consumer', 'product', 'purchase', 'deposit']:
            raise NonExistentTable(table)

        if table is 'consumer':
            cur.row_factory = factory(Consumer)
        elif table is 'product':
            cur.row_factory = factory(Product)
        elif table is 'purchase':
            cur.row_factory = factory(Purchase)
        elif table is 'deposit':
            cur.row_factory = factory(Deposit)

        if id is not None:
            cur.execute('SELECT * FROM {} WHERE id=?;'.format(table), (id,))
        else:
            cur.execute('SELECT * FROM {} WHERE name=?;'.format(table), (name,))
        res = cur.fetchone()
        if res is None:
            raise ObjectNotFound(table=table, id=id, name=name)
        return res

    def get_all(self, table):
        if table not in ['consumer', 'product', 'purchase', 'deposit']:
            raise NonExistentTable(table)

        cur = self.con.cursor()

        if table is 'consumer':
            cur.row_factory = factory(Consumer)
        elif table is 'product':
            cur.row_factory = factory(Product)
        elif table is 'purchase':
            cur.row_factory = factory(Purchase)
        elif table is 'deposit':
            cur.row_factory = factory(Deposit)

        cur.execute('SELECT * FROM {};'.format(table))
        return cur.fetchall()

    def update_consumer(self, consumer):
        if consumer.id is None:
            raise("Consumer has no id")
        cur = self.con.cursor()

        cur.execute('UPDATE consumer SET name=?, active=?, credit=? \
                    WHERE id=?;', (consumer.name, consumer.active,
                                   consumer.credit, consumer.id))
        self.con.commit()

    def create_deposit(self, consumer, amount):
        time = datetime.datetime.now()
        deposit = Deposit(consumer_id=consumer.id,
                          amount=amount,
                          timestamp=time)
        res = self.insert_object(deposit)
        consumer.credit = consumer.credit + amount
        self.update_consumer(consumer)
