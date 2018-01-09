#!/usr/bin/env python3

import collections
import datetime
import os
import pdb
import sqlite3
from math import floor

from backend import models
from .validation import FieldBasedException, InputException, to_dict


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


class InvalidDates(FieldBasedException):

    def __init__(self):
        InputException.__init__(self)


class OnlyOneRowAllowed(FieldBasedException):

    def __init__(self):
        InputException.__init__(self)


class ConsumerNeedsCredentials(FieldBasedException):

    def __init__(self):
        InputException.__init__(self)


class ProductNotCountable(FieldBasedException):

    def __init__(self):
        InputException.__init__(self)


class DuplicateObject(FieldBasedException):

    def __init__(self, field):
        FieldBasedException.__init__(self, field)


class CanOnlyBeRevokedOnce(FieldBasedException):

    def __init__(self):
        FieldBasedException.__init__(self, 'revoked')


class NotRevocable(FieldBasedException):

    def __init__(self, product):
        FieldBasedException.__init__(self, product.name)


def factory(cls):
    """ Helper function for ORM Mapping """
    def fun(cursor, row):
        p = cls()
        for idx, col in enumerate(cursor.description):
            setattr(p, col[0], row[idx])
        return p
    return fun


class DatabaseApi(object):

    def __init__(self, sqlite3_connection, configuration):
        self.con = sqlite3_connection
        self.USE_KARMA = configuration['USE_KARMA']
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

            if object.id is not None:
                res = cur.execute(
                    'SELECT 1 FROM {} WHERE {}=? AND id!=?;'.format(
                        table, field_name),
                    (getattr(object, field_name), object.id)
                )
            else:
                res = cur.execute(
                    'SELECT 1 FROM {} WHERE {}=?;'.format(
                        table, field_name),
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

    def _calculate_product_price(self, base_price, karma):
        pricecategories = self.list_pricecategories()
        bounds = {}
        percent = 0
        for scale in pricecategories:
            bounds[scale.price_lower_bound] = scale.additional_percent

        bounds = collections.OrderedDict(sorted(bounds.items()))

        for bound in bounds:
            if base_price >= bound:
                percent = bounds[bound]
            else:
                break

        return floor(base_price * (1 + percent * (-karma + 10) / 2000))

    def setAdmin(self, consumer, department, admin):
        self._check_foreign_key(consumer, 'id', 'consumers')
        self._check_foreign_key(department, 'id', 'departments')

        cur = self.con.cursor()
        department = self.get_department(id=department.id)
        consumer = self.get_consumer(id=consumer.id)
        adminroles = self.getAdminroles(consumer)#

        # Check, if the consumer is admin for this department
        isAdmin = department.id in [a.department_id for a in adminroles]

        # Case one: Make consumer admin
        if admin and not isAdmin:
            if consumer.email is not None and consumer.password is not None:
                adminrole = models.AdminRole(consumer_id=consumer.id,
                                      department_id=department.id,
                                      timestamp=datetime.datetime.now())
                cur.execute('INSERT INTO adminroles '
                            '(consumer_id, department_id, timestamp) '
                            'VALUES(?,?,?);',
                            (adminrole.consumer_id,
                             adminrole.department_id,
                             adminrole.timestamp)
                            )
                self.con.commit()
            else:
                raise ConsumerNeedsCredentials()

        elif not admin and isAdmin:
            cur.execute('DELETE FROM adminroles WHERE consumer_id = ? '
                        'AND department_id = ?;',
                        (consumer.id, department.id)
                        )
            self.con.commit()

    def getAdminroles(self, consumer):
        self._check_foreign_key(consumer, 'id', 'consumers')
        cur = self.con.cursor()
        cur.row_factory = factory(models.AdminRole)
        res = cur.execute('SELECT * FROM adminroles '
                          'WHERE consumer_id = ?;', (consumer.id, )
                         )
        return cur.fetchall()

    def _simple_update(self, cur, object, table, updateable_fields):
        params = []
        query_parts = []
        log_string = []

        for field in updateable_fields:
            if getattr(object, field) is None:
                continue
            query_parts.append('{}=?'.format(field))
            params.append(getattr(object, field))
            log_string.append('{}={}'.format(field, getattr(object, field)))

        if len(query_parts) == 0:
            return

        res1 = cur.execute(
            'UPDATE {} SET {} WHERE id=?;'
            .format(table, ', '.join(query_parts)),
            params + [object.id]
        )
        if res1.rowcount != 1:
            self.con.rollback()
            raise ObjectNotFound()

        for change in log_string:
            change.replace("True", "1")
            change.replace("False", "0")
            res2 = cur.execute(
                'INSERT INTO logs (table_name, updated_id, '
                'data_inserted, timestamp) '
                'VALUES(?,?,?,?);',
                (table, object.id, change, datetime.datetime.now())
            )
            if res2.rowcount != 1:
                self.con.rollback()
                raise ObjectNotFound()

    def insert_workactivity(self, workactivity):
        cur = self.con.cursor()

        self._assert_mandatory_fields(workactivity, ['name'])
        self._check_uniqueness(workactivity, 'workactivities',
                               ['name'])
        self._assert_forbidden_fields(workactivity, ['id'])


        cur.execute('INSERT INTO workactivities '
                    '(name) VALUES(?);', (workactivity.name, )
                    )
        self.con.commit()

    def insert_activity(self, activity):
        cur = self.con.cursor()

        self._assert_mandatory_fields(activity,
                                      ['workactivity_id',
                                       'date_deadline',
                                       'date_event',
                                       'created_by'])

        self._assert_forbidden_fields(activity,
                                      ['id', 'date_created', 'active'])
        self._check_foreign_key(activity, 'created_by', 'consumers')

        activity.date_created = datetime.datetime.now()
        activity.active = True

        cur.execute('INSERT INTO activities '
                    '(created_by, workactivity_id, active, '
                    'date_created, date_deadline, date_event) '
                    'VALUES(?,?,?,?,?,?);', (
                    activity.created_by, activity.workactivity_id,
                    activity.active, activity.date_created,
                    activity.date_deadline, activity.date_event)
                )

        self.con.commit()



        self.con.commit()

    def insert_product(self, product):
        cur = self.con.cursor()

        self._assert_mandatory_fields(
            product, ['name', 'countable', 'price',
                      'department_id', 'revocable']
        )
        self._assert_forbidden_fields(product, ['id', 'active', 'stock'])
        self._check_uniqueness(product, 'products', ['name'])
        self._check_foreign_key(product, 'department_id', 'departments')

        if product.image is None:
            product.image = 'default.png'

        product.stock = 0 if product.countable else None

        product.active = True

        cur.execute(
            'INSERT INTO products '
            '(name, active, stock, price, department_id, '
            'revocable, countable, image, barcode) '
            'VALUES (?,?,?,?,?,?,?,?,?);',
            (product.name, product.active, product.stock,
             product.price, product.department_id,
             product.revocable, product.countable,
             product.image, product.barcode)
        )
        self.con.commit()

    def insert_consumer(self, consumer):
        cur = self.con.cursor()

        self._assert_mandatory_fields(
            consumer, ['name'])
        self._assert_forbidden_fields(consumer,
                                      ['id', 'credit', 'active', 'karma'])
        self._check_uniqueness(consumer, 'consumers', ['name'])

        if consumer.email is not None:
            self._check_uniqueness(consumer, 'consumers', ['email'])

        if consumer.studentnumber is not None:
            self._check_uniqueness(consumer, 'consumers', ['studentnumber'])

        consumer.credit = 0
        consumer.active = True
        consumer.karma = 0

        cur.execute(
            'INSERT INTO consumers '
            '(name, active, credit, karma, email, password, studentnumber) '
            'VALUES (?,?,?,?,?,?,?);',
            (consumer.name, consumer.active, consumer.credit,
             consumer.karma, consumer.email, consumer.password,
             consumer.studentnumber)
        )
        self.con.commit()

    def insert_department(self, department):
        cur = self.con.cursor()

        self._assert_mandatory_fields(
            department, ['name', 'budget'])
        self._assert_forbidden_fields(department, ['id'])
        self._check_uniqueness(department, 'departments', ['name'])
        department.income_base = 0
        department.income_karma = 0
        department.expenses = 0

        cur.execute(
            'INSERT INTO departments '
            '(name, income_base, income_karma, expenses, budget) '
            'VALUES (?,?,?,?,?);',
            (department.name, department.income_base,
             department.income_karma, department.expenses, department.budget)
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
            purchase, ['id', 'timestamp', 'revoked',
                       'paid_base_price_per_product',
                       'paid_karma_per_product']
        )

        # TODO: purchase should be only allowed if the product and the consumer
        #       is active
        purchase.timestamp = datetime.datetime.now()
        purchase.revoked = False

        self._check_foreign_key(purchase, 'consumer_id', 'consumers')
        self._check_foreign_key(purchase, 'product_id', 'products')

        consumer = self.get_consumer(purchase.consumer_id)
        product = self.get_product(purchase.product_id)
        if self.USE_KARMA:
            price_to_pay = self._calculate_product_price(product.price,
                                                         consumer.karma)
        else:
            price_to_pay = product.price

        cur.execute(
            'INSERT INTO purchases('
            '    consumer_id, '
            '    product_id, '
            '    comment, '
            '    revoked, '
            '    timestamp,'
            '    amount,'
            '    paid_base_price_per_product,'
            '    paid_karma_per_product) '
            'VALUES ('
            '    ?, '
            '    ?, '
            '    ?, '
            '    ?, '
            '    ?, '
            '    ?, '
            '    ?, '
            '    ? '
            ');',
            (purchase.consumer_id,
             purchase.product_id,
             purchase.comment,
             purchase.revoked,
             purchase.timestamp,
             purchase.amount,
             product.price,
             price_to_pay - product.price)
        )

        cur.execute(
            'UPDATE consumers '
            'SET credit = credit - ?*?'
            'WHERE id=?;',
            (purchase.amount,
             price_to_pay,
             purchase.consumer_id)
        )
        if product.countable:
            cur.execute(
                'UPDATE products '
                'SET stock = stock - ?'
                'WHERE id=?;',
                (purchase.amount,
                 product.id)
            )

            s = models.StockHistory(product_id=product.id,
                             new_stock=product.stock - purchase.amount,
                             timestamp=datetime.datetime.now())

            cur.execute(
                'INSERT INTO stockhistory (product_id, new_stock, timestamp) '
                'VALUES (?,?,?);',
                (s.product_id, s.new_stock, s.timestamp)
            )

        cur.execute('UPDATE departments SET '
                    'income_base = income_base + ?*?, '
                    'income_karma = income_karma + ?*? '
                    'WHERE id=?;',
                    (purchase.amount,
                     product.price,
                     purchase.amount,
                     price_to_pay - product.price,
                     product.department_id)
                    )

        self.con.commit()

    def insert_deposit(self, deposit):
        cur = self.con.cursor()

        self._assert_mandatory_fields(
            deposit, ['consumer_id', 'amount', 'comment'])
        self._assert_forbidden_fields(deposit, ['id', 'timestamp'])

        # default values
        deposit.timestamp = datetime.datetime.now()

        self._check_foreign_key(deposit, 'consumer_id', 'consumers')

        cur.execute(
            'INSERT INTO deposits (consumer_id, amount, comment, timestamp) '
            'VALUES (?,?,?,?);',
            (deposit.consumer_id, deposit.amount,
             deposit.comment, deposit.timestamp)
        )

        cur.execute(
            'UPDATE consumers '
            'SET credit = credit + ? '
            'WHERE id=?;',
            (deposit.amount,
             deposit.consumer_id)
        )

        cur.execute(
            'UPDATE banks '
            'SET credit = credit + ? ;',
            (deposit.amount, )
        )

        self.con.commit()

    def get_activity(self, id):
        return self._get_one(model=models.Activity, table='activities', id=id)

    def get_workactivity(self, id):
        return self._get_one(model=models.WorkActivity, table='workactivities', id=id)

    def get_consumer(self, id):
        return self._get_one(model=models.Consumer, table='consumers', id=id)

    def get_product(self, id):
        return self._get_one(model=models.Product, table='products', id=id)

    def get_purchase(self, id):
        return self._get_one(model=models.Purchase, table='purchases', id=id)

    def get_deposit(self, id):
        return self._get_one(model=models.Deposit, table='deposits', id=id)

    def get_department(self, id):
        return self._get_one(model=models.Department, table='departments', id=id)

    def get_payoff(self, id):
        return self._get_one(model=models.Payoff, table='payoffs', id=id)

    def get_bank(self):
        return self._get_one(model=models.Bank, table='banks', id=1)

    def _get_one(self, model, table, id):
        cur = self.con.cursor()
        cur.row_factory = factory(model)
        cur.execute('SELECT * FROM {} WHERE id=?;'.format(table), (id,))

        res = cur.fetchone()
        if res is None:
            raise ObjectNotFound()
        return res

    def get_consumer_by_email(self, email):
        cur = self.con.cursor()
        cur.row_factory = factory(models.Consumer)
        cur.execute('SELECT * FROM consumers WHERE email=?;', (email, ))
        res = cur.fetchall()
        if res is None or len(res) > 1:
            raise ObjectNotFound()
        return res[0]

    def get_activity_feedbacks(self, activity):
        self._check_foreign_key(activity, 'id', 'activities')
        consumers = self.list_consumers()

        cur = self.con.cursor()
        cur.row_factory = factory(Feedback)

        feedbacks = {}
        for consumer in consumers:
            feedbacks[consumer.id] = []

        cur.execute('SELECT * FROM feedbacks  WHERE activity_id=?;',
                    (activity.id, )
                   )

        res = cur.fetchall()

        for feedback in res:
            feedbacks[feedback.consumer_id].append(to_dict(feedback))

        return feedbacks


    def getDepartmentStatistics(self, id):
        statistics = {}
        statistics['department_id'] = id
        statistics['top_products'] = self._get_top_products(department_id=id,
                                                          num_products=10)
        statistics['purchase_times'] = self._get_purchase_times(
          department_id=id)

        return statistics

    def _get_top_products(self, department_id, num_products):
        cur = self.con.cursor()
        cur.execute('SELECT product_id, count(product_id) '
                  'FROM purchases GROUP BY product_id '
                  'ORDER BY count(product_id) '
                  'DESC LIMIT ?;', (num_products,)
                  )
        return cur.fetchall()

    def _get_purchase_times(self, department_id):
        num_purchases = 2000
        purchases = self._list_purchases_department(
          department_id=department_id, limit=num_purchases)
        ranges = [[i, i + 1] for i in range(0, 24)]
        labels = [str(i + 1) for i in range(0, 24)]
        labels = []

        for i in range(0, 24):
          ranges.append([i, i + 1])
          labels.append(str(i + 1))

        times = [0 for i in range(0, len(labels))]

        for purchase in purchases:
          i = 0
          for r in ranges:
              if purchase.timestamp.hour in range(r[0], r[1] + 1):
                  times[i] += 1
                  break
              i += 1
        times = [i * 100 / num_purchases for i in times]
        out = {}
        out['labels'] = labels
        out['data'] = times

        return out

    def get_purchases_of_consumer(self, id):
        return self._get_consumer_data(model=Purchase,
                                       table='purchases', id=id)

    def get_deposits_of_consumer(self, id):
        return self._get_consumer_data(model=Deposit, table='deposits', id=id)

    def _get_consumer_data(self, model, table, id):
        cur = self.con.cursor()
        cur.row_factory = factory(model)
        cur.execute(
            'SELECT * FROM {} WHERE consumer_id=?;'.format(table), (id,))
        return cur.fetchall()

    def get_top_products(self, num_products):
        cur = self.con.cursor()
        cur.execute('SELECT product_id, count(product_id) '
                    'FROM purchases GROUP BY product_id '
                    'ORDER BY count(product_id) '
                    'DESC LIMIT ?;', (num_products,)
                    )
        return cur.fetchall()

    def get_stockhistory(self, product_id, date_start=None, date_end=None):
        cur = self.con.cursor()
        cur.row_factory = factory(models.StockHistory)

        p = self.get_product(id=product_id)

        if not p.countable:
            raise ProductNotCountable()

        if date_start is None or date_end is None:
            date_start = datetime.datetime.now() - datetime.timedelta(weeks=4)
            date_end = datetime.datetime.now()

        cur.execute('SELECT * FROM stockhistory WHERE product_id=? '
                    'AND timestamp BETWEEN ? AND ?;',
                    (product_id, date_start, date_end)
                    )
        return cur.fetchall()

    def get_favorite_products(self, id):
        cur = self.con.cursor()
        cur.row_factory = factory(models.Purchase)
        cur.execute(
            'SELECT * FROM purchases WHERE consumer_id=? AND revoked=0 \
            GROUP BY product_id ORDER BY COUNT(product_id) DESC \
            LIMIT 10', (id,))
        return cur.fetchall()

    def get_karma_history(self, id):
        cur = self.con.cursor()
        cur.row_factory = factory(Log)
        cur.execute(
            'SELECT * FROM logs WHERE table_name=?'
            'AND updated_id=? '
            'AND data_inserted LIKE ? '
            'ORDER BY id DESC '
            ' LIMIT 100', ('consumers', id, 'karma=%'))
        return cur.fetchall()

    def list_consumers(self):
        return self._list(model=models.Consumer, table='consumers', limit=None)

    def list_products(self):
        return self._list(model=models.Product, table='products', limit=None)

    def list_purchases(self, limit=None):
        return self._list(model=models.Purchase, table='purchases', limit=limit)

    def list_deposits(self, limit=None):
        return self._list(model=models.Deposit, table='deposits', limit=limit)

    def list_departments(self):
        return self._list(model=models.Department, table='departments', limit=None)

    def list_pricecategories(self):
        return self._list(model=models.PriceCategory,
                          table='pricecategories',
                          limit=None)

    def list_payoffs(self, limit=None):
        return self._list(model=models.Payoff, table='payoffs', limit=limit)

    def list_logs(self, limit=None):
        return self._list(model=models.Log, table='logs', limit=limit)

    def list_workactivities(self):
        return self._list(model=models.WorkActivity, table='workactivities', limit=None)

    def list_activities(self):
        return self._list(model=models.Activity, table='activities', limit=None)

    def list_banks(self):
        return self._list(model=models.Bank, table='banks', limit=None)

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

    def _list_purchases_department(self, department_id, limit=None):
        cur = self.con.cursor()
        cur.row_factory = factory(models.Purchase)
        if limit is None:
            cur.execute('SELECT * FROM purchases '
                        'WHERE product_id IN (SELECT id FROM products '
                        'WHERE department_id=?) ORDER BY id;', (department_id,))

        else:
            limit = int(limit)
            cur.execute('SELECT * FROM purchases '
                        'WHERE product_id IN (SELECT id FROM products '
                        'WHERE department_id=?) ORDER BY id DESC LIMIT ?;', (department_id, limit))
        return cur.fetchall()

    def update_product(self, product):
        cur = self.con.cursor()

        self._assert_mandatory_fields(product, ['id'])
        # TODO: what happens here if product.name is None?
        self._check_uniqueness(product, 'products', ['name'])

        self._simple_update(
            cur=cur, object=product, table='products',
            updateable_fields=['name', 'price', 'active', 'barcode',
                               'stock', 'countable', 'department_id', 'image']
        )

        self.con.commit()

    def update_consumer(self, consumer):
        self._assert_mandatory_fields(consumer, ['id'])
        self._assert_forbidden_fields(consumer, ['credit'])
        self._check_uniqueness(consumer, 'consumers', ['name'])
        cur = self.con.cursor()

        self._simple_update(
            cur=cur, object=consumer, table='consumers',
            updateable_fields=['name', 'active', 'karma', 'email',
                               'password', 'studentnumber']
        )
        self.con.commit()

    def update_deed(self, deed):
        self._assert_mandatory_fields(deed, ['id'])
        cur = self.con.cursor()

        self._simple_update(
            cur=cur, object=deed, table='deeds',
            updateable_fields=['name', 'timestamp', 'done']
        )
        self.con.commit()

    def update_participation(self, participation):
        self._assert_mandatory_fields(participation, ['id'])
        self._check_foreign_key(participation, 'flag_id', 'flags')
        cur = self.con.cursor()

        self._simple_update(
            cur=cur, object=participation, table='participations',
            updateable_fields=['flag_id']
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


    def update_workactivity(self, workactivity):
        self._assert_mandatory_fields(workactivity, ['id'])
        self._check_uniqueness(workactivity, 'workactivities',
                               ['name'])

        cur = self.con.cursor()
        self._simple_update(cur, object=workactivity, table='workactivities',
                            updateable_fields=['name'])

        self.con.commit()

    def update_activity(self, activity):
        self._assert_mandatory_fields(activity, ['id'])

        apiActivity = self.get_activity(id=activity.id)
        try:
            date_event = getattr(activity, date_event)
        except:
            date_event = apiActivity.date_event

        try:
            date_deadline = getattr(activity, date_deadline)
        except:
            date_deadline = apiActivity.date_deadline


        if not (date_event > date_deadline > apiActivity.date_created):
            raise InvalidDates()

        cur = self.con.cursor()

        self._simple_update(cur, object=activity, table='activities',
                            updateable_fields=['date_deadline', 'date_event', 'active'])

        self.con.commit()

    def update_purchase(self, purchase):
        self._assert_mandatory_fields(purchase, ['id'])
        self._assert_forbidden_fields(purchase, ['consumer_id', 'amount',
                                                 'product_id', 'timestamp',
                                                 'paid_base_price_per_product',
                                                 'paid_karma_per_product'])

        if purchase.revoked is None or not purchase.revoked:
            # nothing to do
            # TODO: maybe we should return something like "nothing to do"
            return

        dbpur = self.get_purchase(id=purchase.id)

        product = self.get_product(id=dbpur.product_id)
        if product.revocable == 0:
            raise NotRevocable(product)

        cur = self.con.cursor()

        if purchase.revoked and dbpur.revoked:
            raise CanOnlyBeRevokedOnce()

        return_money = dbpur.amount * \
            (dbpur.paid_base_price_per_product +
             dbpur.paid_karma_per_product)

        return_base = dbpur.amount * dbpur.paid_base_price_per_product
        return_karma = dbpur.amount * dbpur.paid_karma_per_product

        cur.execute('UPDATE consumers '
                    'SET credit=credit + {} WHERE id=?;'.format(
                        return_karma + return_base),
                    (dbpur.consumer_id, )
                    )

        if product.countable:
            cur.execute('UPDATE products '
                        'SET stock=stock + ? WHERE id=?;',
                        (dbpur.amount, dbpur.product_id)
                        )

        cur.execute('UPDATE departments '
                    'SET income_base = income_base - {} , '
                    'income_karma = income_karma - {} '
                    'WHERE id=?;'.format(return_base, return_karma),
                    (product.department_id, )
                    )

        self._simple_update(cur, object=purchase, table='purchases',
                            updateable_fields=['revoked', 'comment'])

        self.con.commit()
