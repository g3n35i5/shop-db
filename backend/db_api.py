#!/usr/bin/env python3

import datetime
import pdb
import sqlite3

from .models import (Bank, Consumer, Department, Deposit, Payoff, Product,
                     Purchase)
from .validation import FieldBasedException, InputException

# convert booleans since sqlite3 has no booleans
# see: https://www.sqlite.org/datatype3.html#boolean_datatype
sqlite3.register_adapter(bool, int)
sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))


class ForeignKeyNotExisting(FieldBasedException):

    def __init__(self, field):
        FieldBasedException.__init__(self, field)


class FieldIsNone(FieldBasedException):

    def __init__(self, field):
        FieldBasedException.__init__(self, field)


class ForbiddenField(FieldBasedException):

    def __init__(self, field):
        FieldBasedException.__init__(self, field)


class ObjectNotFound(InputException):

    def __init__(self):
        InputException.__init__(self)


class DuplicateObject(FieldBasedException):

    def __init__(self, field):
        FieldBasedException.__init__(self, field)


class CanOnlyBeRevokedOnce(FieldBasedException):

    def __init__(self):
        FieldBasedException.__init__(self, 'revoked')


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
                raise FieldIsNone(field_name)

    def _assert_forbidden_fields(self, object, fields):
        for field_name in fields:
            if getattr(object, field_name, None) is not None:
                raise ForbiddenField(field=field_name)

    def _check_uniqueness(self, object, table, fields):
        cur = self.con.cursor()
        for field_name in fields:
            res = cur.execute(
                'SELECT 1 FROM {} WHERE {}=?'.format(table, field_name),
                (getattr(object, field_name),)
            )
            if res.fetchone() is not None:
                raise DuplicateObject(field=field_name)

    def _check_foreign_key(self, object, foreign_key, foreign_table):
        cur = self.con.cursor()

        # Since the foreign key exception of sqlite3 has no information
        # which foreign key constrait was breaked, we have to check
        # that by selecting the object.
        c = cur.execute('SELECT 1 FROM {} WHERE id=?;'.format(foreign_table),
                        (getattr(object, foreign_key),))

        if c.fetchone() is None:
            raise ForeignKeyNotExisting(foreign_key)

    def _simple_update(self, cur, object, table, updateable_fields):
        params = []
        query_parts = []

        for field in updateable_fields:
            if getattr(object, field) is None:
                continue
            query_parts.append('{}=?'.format(field))
            params.append(getattr(object, field))

        if len(query_parts) == 0:
            return

        res = cur.execute(
            'UPDATE {} SET {} WHERE id=?'
            .format(table, ', '.join(query_parts)),
            params + [object.id]
        )

        if res.rowcount != 1:
            self.con.rollback()
            raise ObjectNotFound()

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

    def insert_department(self, department):
        cur = self.con.cursor()

        self._assert_mandatory_fields(
            department, ['name', 'budget'])
        self._assert_forbidden_fields(department, ['id'])
        self._check_uniqueness(department, 'departments', ['name'])

        cur.execute(
            'INSERT INTO departments (name, income, expenses, budget) '
            'VALUES (?,?,?,?);',
            (department.name, 0, 0, department.budget)
        )
        self.con.commit()

    def insert_payoff(self, payoff):
        cur = self.con.cursor()

        self._assert_mandatory_fields(payoff, ['department_id',
                                               'amount',
                                               'comment'])
        self._assert_forbidden_fields(
            payoff, ['id', 'timestamp', 'revoked']
        )

        payoff.timestamp = datetime.datetime.now()
        payoff.revoked = False

        self._check_foreign_key(payoff, 'department_id', 'departments')

        cur.execute(
            'INSERT INTO payoffs('
            '    department_id, '
            '    comment, '
            '    amount, '
            '    revoked,'
            '    timestamp) '
            'VALUES ('
            '    ?, '
            '    ?, '
            '    ?, '
            '    ?, '
            '    ? '
            ');',
            (payoff.department_id,
             payoff.comment,
             payoff.amount,
             payoff.revoked,
             payoff.timestamp)
        )

        cur.execute(
            'UPDATE departments '
            'SET expenses = expenses + ? '
            'WHERE id=?;',
            (payoff.amount,
             payoff.department_id)
        )

        cur.execute(
            'UPDATE banks '
            'SET credit = credit - ?; ',
            (payoff.amount, )
        )

        self.con.commit()

    def insert_purchase(self, purchase):
        cur = self.con.cursor()

        self._assert_mandatory_fields(purchase, ['product_id',
                                                 'consumer_id',
                                                 'amount',
                                                 'comment'])
        self._assert_forbidden_fields(
            purchase, ['id', 'timestamp', 'revoked', 'paid_price_per_product']
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
            '    comment, '
            '    revoked, '
            '    timestamp,'
            '    amount,'
            '    paid_price_per_product) '
            'VALUES ('
            '    ?, '
            '    ?, '
            '    ?, '
            '    ?, '
            '    ?, '
            '    ?, '
            '    (SELECT price from product where id=?)'
            ');',
            (purchase.consumer_id,
             purchase.product_id,
             purchase.comment,
             purchase.revoked,
             purchase.timestamp,
             purchase.amount,
             purchase.product_id)
        )

        cur.execute(
            'UPDATE consumer '
            'SET credit = credit - ?*(SELECT price from product where id=?) '
            'WHERE id=?;',
            (purchase.amount,
             purchase.product_id,
             purchase.consumer_id)
        )

        self.con.commit()

    def insert_deposit(self, deposit):
        cur = self.con.cursor()

        self._assert_mandatory_fields(
            deposit, ['consumer_id', 'amount', 'comment'])
        self._assert_forbidden_fields(deposit, ['id', 'timestamp'])

        # default values
        deposit.timestamp = datetime.datetime.now()

        self._check_foreign_key(deposit, 'consumer_id', 'consumer')

        cur.execute(
            'INSERT INTO deposit (consumer_id, amount, comment, timestamp) '
            'VALUES (?,?,?,?);',
            (deposit.consumer_id, deposit.amount,
             deposit.comment, deposit.timestamp)
        )

        cur.execute(
            'UPDATE consumer '
            'SET credit = credit + ? '
            'WHERE id=?;',
            (deposit.amount,
             deposit.consumer_id)
        )

        self.con.commit()

    def get_consumer(self, id):
        return self._get_one(model=Consumer, table='consumer', id=id)

    def get_product(self, id):
        return self._get_one(model=Product, table='product', id=id)

    def get_purchase(self, id):
        return self._get_one(model=Purchase, table='purchase', id=id)

    def get_deposit(self, id):
        return self._get_one(model=Deposit, table='deposit', id=id)

    def get_department(self, id):
        return self._get_one(model=Department, table='departments', id=id)

    def get_payoff(self, id):
        return self._get_one(model=Payoff, table='payoffs', id=id)

    def get_bank(self):
        return self._get_one(model=Bank, table='banks', id=1)

    def _get_one(self, model, table, id):
        cur = self.con.cursor()
        cur.row_factory = factory(model)
        cur.execute('SELECT * FROM {} WHERE id=?;'.format(table), (id,))

        res = cur.fetchone()
        if res is None:
            raise ObjectNotFound()
        return res

    def get_purchases_of_consumer(self, id):
        return self._get_consumer_data(model=Purchase, table='purchase', id=id)

    def get_deposits_of_consumer(self, id):
        return self._get_consumer_data(model=Deposit, table='deposit', id=id)

    def _get_consumer_data(self, model, table, id):
        cur = self.con.cursor()
        cur.row_factory = factory(model)
        cur.execute(
            'SELECT * FROM {} WHERE consumer_id=?;'.format(table), (id,))
        return cur.fetchall()

    def get_favorite_products(self, id):
        cur = self.con.cursor()
        cur.row_factory = factory(Purchase)
        cur.execute(
            'SELECT * FROM purchase WHERE consumer_id=? AND revoked=0 \
            GROUP BY product_id ORDER BY COUNT(product_id) DESC \
            LIMIT 10', (id,))
        return cur.fetchall()

    def list_consumers(self):
        return self._list(model=Consumer, table='consumer', limit=None)

    def list_products(self):
        return self._list(model=Product, table='product', limit=None)

    def list_purchases(self, limit=None):
        return self._list(model=Purchase, table='purchase', limit=limit)

    def list_deposits(self, limit=None):
        return self._list(model=Deposit, table='deposit', limit=limit)

    def list_departments(self):
        return self._list(model=Department, table='departments', limit=None)

    def list_payoffs(self, limit=None):
        return self._list(model=Payoff, table='payoffs', limit=limit)

    def list_banks(self):
        return self._list(model=Bank, table='banks', limit=None)

    def _list(self, model, table, limit):
        cur = self.con.cursor()
        cur.row_factory = factory(model)
        if limit is None:
            cur.execute('SELECT * FROM {};'.format(table))
        else:
            limit = int(limit)
            cur.execute(
                'SELECT * FROM {} ORDER BY id  DESC LIMIT ?;'.format(
                    table), (limit,)
            )
        return cur.fetchall()

    def update_product(self, product):
        cur = self.con.cursor()

        self._assert_mandatory_fields(product, ['id'])
        # TODO: what happens here if product.name is None?
        self._check_uniqueness(product, 'product', ['name'])

        self._simple_update(
            cur=cur, object=product, table='product',
            updateable_fields=['name', 'price', 'active',
                               'on_stock']
        )

        self.con.commit()

    def update_consumer(self, consumer):
        self._assert_mandatory_fields(consumer, ['id'])
        self._assert_forbidden_fields(consumer, ['credit'])
        self._check_uniqueness(consumer, 'consumer', ['name'])
        cur = self.con.cursor()

        self._simple_update(
            cur=cur, object=consumer, table='consumer',
            updateable_fields=['name', 'active']
        )
        self.con.commit()

    def update_payoff(self, payoff):
        self._assert_mandatory_fields(payoff, ['id'])
        self._assert_forbidden_fields(
            payoff, ['department_id',
                     'amount']
        )
        if payoff.revoked is None or not payoff.revoked:
            # nothing to do
            # TODO: maybe we should return something like "nothing to do"
            return

        cur = self.con.cursor()

        cur.execute(
            'WITH p AS ('
            '    SELECT department_id, amount '
            '    FROM payoffs WHERE id=? and revoked=0'
            ') '
            'UPDATE banks '
            'SET credit=credit+(SELECT amount FROM p);',
            (payoff.id, )
        )

        cur.execute(
            'WITH p AS ('
            '    SELECT department_id, amount '
            '    FROM payoffs WHERE id=? and revoked=0'
            ') '
            'UPDATE departments '
            'SET expenses=expenses-(SELECT amount FROM p);',
            (payoff.id, )
        )

        if cur.rowcount == 0:
            self.con.rollback()
            raise CanOnlyBeRevokedOnce()

        self._simple_update(cur, object=payoff, table='payoffs',
                            updateable_fields=['revoked', 'comment'])

        self.con.commit()

    def update_purchase(self, purchase):
        self._assert_mandatory_fields(purchase, ['id'])
        self._assert_forbidden_fields(purchase, ['consumer_id', 'amount',
                                                 'product_id', 'timestamp',
                                                 'paid_price_per_product'])

        if purchase.revoked is None or not purchase.revoked:
            # nothing to do
            # TODO: maybe we should return something like "nothing to do"
            return

        cur = self.con.cursor()
        cur.execute(
            'WITH p AS ('
            '    SELECT consumer_id, amount, paid_price_per_product '
            '    FROM purchase WHERE id=? and revoked=0'
            ') '
            'UPDATE consumer '
            'SET credit=credit+(SELECT amount*paid_price_per_product FROM p) '
            'WHERE id IN (SELECT consumer_id FROM p);',
            (purchase.id, )
        )

        if cur.rowcount == 0:
            self.con.rollback()
            raise CanOnlyBeRevokedOnce()

        self._simple_update(cur, object=purchase, table='purchase',
                            updateable_fields=['revoked', 'comment'])

        self.con.commit()
