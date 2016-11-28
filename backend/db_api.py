#!/usr/bin/env python3

import sqlite3
from .models import Consumer, Product, Purchase, Deposit
import pdb
import datetime

# convert booleans since sqlite3 has no booleans
# see: https://www.sqlite.org/datatype3.html#boolean_datatype
sqlite3.register_adapter(bool, int)
sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))


class DatabaseApiException(Exception):
    def __init__(self, model):
        self.model = model


class ForeignKeyNotExisting(DatabaseApiException):
    def __init__(self, foreign_key, foreign_id):
        self.foreign_key = foreign_key
        self.foreign_id = foreign_id

    def __str__(self):
        return 'Foreign key {0.foreign_key} with ' + \
               'id={0.foreign_id} does not exist.'.format(self)


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


class ForbiddenField(DatabaseApiException):
    def __init__(self, model, field):
        self.model = model
        self.field = field

    def __str__(self):
        return '{0.model.__name__}: field {0.field}' + \
               'is not allowed'.format(self)


class ObjectNotFound(DatabaseApiException):
    def __init__(self, model, id):
        self.model = model
        self.id = id

    def __str__(self):
        return '{0.model.__name__} with ' + \
            'id={0.id} not found.'.format(self)


class DuplicateObject(DatabaseApiException):
    def __init__(self, model, unique_field_name, unique_field_value):
        self.model = model
        self.unique_field_name = unique_field_name
        self.unique_field_value = unique_field_value

    def __str__(self):
        return 'There is already a {0.model.__name__} with ' + \
               '{0.unique_field_name}="self.unique_field_value"'


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
        self.con.execute('PRAGMA foreign_keys = ON;')

    def _assert_mandatory_fields(self, object, fields):
        for field_name in fields:
            if getattr(object, field_name, None) is None:
                raise FieldIsNone(model=type(object), field=field_name)

    def _assert_forbidden_fields(self, object, fields):
        for field_name in fields:
            if getattr(object, field_name, None) is not None:
                raise ForbiddenField(model=type(object), field=field_name)

    def _check_uniqueness(self, object, table, fields):
        cur = self.con.cursor()
        for field_name in fields:
            res = cur.execute(
                'SELECT 1 FROM {} WHERE {}=?'.format(table, field_name),
                (getattr(object, field_name),)
            )
            if res.fetchone() is not None:
                raise DuplicateObject(
                    model=type(object),
                    unique_field_name=field_name,
                    unique_field_value=getattr(object, field_name)
                )

    def _check_foreign_key(self, object, foreign_key, foreign_table):
        cur = self.con.cursor()

        # Since the foreign key exception of sqlite3 has no information
        # which foreign key constrait was breaked, we have to check
        # that by selecting the object.
        c = cur.execute('SELECT 1 FROM {} WHERE id=?;'.format(foreign_table),
                        (getattr(object, foreign_key),))

        if c.fetchone() is None:
            raise ForeignKeyNotExisting(foreign_key,
                                        getattr(object, foreign_key))

    def insert_product(self, product):
        cur = self.con.cursor()

        self._assert_mandatory_fields(
            product, ['name', 'active', 'on_stock', 'price']
        )
        self._assert_forbidden_fields(product, ['id'])
        self._check_uniqueness(product, 'product', ['name'])

        cur.execute(
            'INSERT INTO product (name, active, on_stock, price) '
            'VALUES (?,?,?,?);',
            (product.name, product.active, product.on_stock, product.price)
        )
        self.con.commit()

    def insert_consumer(self, consumer):
        cur = self.con.cursor()

        self._assert_mandatory_fields(consumer, ['name', 'active', 'credit'])
        self._assert_forbidden_fields(consumer, ['id'])
        self._check_uniqueness(consumer, 'consumer', ['name'])

        cur.execute(
            'INSERT INTO consumer (name, active, credit) '
            'VALUES (?,?,?);',
            (consumer.name, consumer.active, consumer.credit)
        )
        self.con.commit()

    def insert_purchase(self, purchase):
        cur = self.con.cursor()

        self._assert_mandatory_fields(purchase, ['product_id', 'consumer_id'])
        self._assert_forbidden_fields(
            purchase, ['id', 'timestamp', 'revoked', 'paid_price']
        )

        # TODO: purchase should be only allowed if the product and the consumer
        #       is active
        purchase.timestamp = datetime.datetime.now()
        purchase.revoked = False

        self._check_foreign_key(purchase, 'consumer_id', 'consumer')
        self._check_foreign_key(purchase, 'product_id', 'product')

        cur.execute(
            'INSERT INTO purchase('
            '    consumer_id, '
            '    product_id, '
            '    revoked, '
            '    timestamp,'
            '    paid_price) '
            'VALUES ('
            '    ?, '
            '    ?, '
            '    ?, '
            '    ?, '
            '    (SELECT price from product where id=?)'
            ');',
            (purchase.consumer_id,
             purchase.product_id,
             purchase.revoked,
             purchase.timestamp,
             purchase.product_id)
        )

        cur.execute(
            'UPDATE consumer '
            'SET credit = credit - (SELECT price from product where id=?) '
            'WHERE id=?;',
            (purchase.product_id,
             purchase.consumer_id)
        )

        self.con.commit()

    def insert_deposit(self, deposit):
        cur = self.con.cursor()

        self._assert_mandatory_fields(deposit, ['consumer_id', 'amount'])
        self._assert_forbidden_fields(deposit, ['id', 'timestamp'])

        # default values
        deposit.timestamp = datetime.datetime.now()

        self._check_foreign_key(deposit, 'consumer_id', 'consumer')

        cur.execute(
            'INSERT INTO deposit (consumer_id, amount, timestamp) '
            'VALUES (?,?,?);',
            (deposit.consumer_id, deposit.amount, deposit.timestamp)
        )

        cur.execute(
            'UPDATE consumer '
            'SET credit = credit + ? '
            'WHERE id=?;',
            (deposit.amount,
             deposit.consumer_id)
        )

        self.con.commit()

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
            if table is not 'deposit':
                cur.execute('SELECT * FROM {} WHERE name=?;'.format(table),
                            (name,))
            else:
                raise 'field name is not available for deposit'
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

    def update_product(self, product):
        cur = self.con.cursor()

        self._assert_mandatory_fields(product, ['id'])
        # TODO: what happens here if product.name is None?
        self._check_uniqueness(product, 'product', ['name'])

        # TODO: maybe we should outsource the query generation
        #       into an own helper function later
        updateable_fields = ['name', 'price', 'active',
                             'on_stock']

        params = []
        query_parts = []

        for field in updateable_fields:
            if getattr(product, field) is None:
                continue
            query_parts.append('{}=?'.format(field))
            params.append(getattr(product, field))

        res = cur.execute(
            'UPDATE product SET {} WHERE id=?'
            .format(', '.join(query_parts)),
            params + [product.id]
        )

        if res.rowcount != 1:
            raise ObjectNotFound(Product, product.id)

    def update_consumer(self, consumer):
        if consumer.id is None:
            raise("Consumer has no id")
        cur = self.con.cursor()

        cur.execute('UPDATE consumer SET name=?, active=?, credit=? \
                    WHERE id=?;', (consumer.name, consumer.active,
                                   consumer.credit, consumer.id))
        self.con.commit()

    def update_purchase(self, purchase):
        if purchase.id is None:
            raise("Purchase has no id")
        cur = self.con.cursor()
        consumer = self.get_one(table='consumer', id=purchase.consumer_id)

        if purchase.revoked is True:
            consumer.credit = consumer.credit + purchase.paid_price
        if purchase.revoked is False:
            consumer.credit = consumer.credit - purchase.paid_price

        self.update_consumer(consumer)
        cur.execute('UPDATE purchase SET revoked=? \
                    WHERE id=?;', (purchase.revoked, purchase.id))
        self.con.commit()
