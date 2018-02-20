#!/usr/bin/env python3

import collections
import datetime
import os
import pdb
import sys
import sqlite3
from math import floor
from operator import itemgetter

import project.backend.models as models
import project.backend.validation as validation
import project.backend.exceptions as exc


# convert booleans since sqlite3 has no booleans
# see: https://www.sqlite.org/datatype3.html#boolean_datatype
sqlite3.register_adapter(bool, int)
sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))


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
        self.configuration = configuration
        self.con = sqlite3_connection
        self.con.execute('PRAGMA foreign_keys = ON;')

    def create_tables(self):
        cursor = self.con.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        if cursor.fetchall():
            sys.exit('You are currently trying to overwrite the '
                     'productive database. This should not happen '
                     'under any circumstances.')

        with open(self.configuration['DATABASE_SCHEMA']) as models:
            schema = models.read()

        self.con.executescript(schema)

    def _assert_mandatory_fields(self, object, fields):
        for field_name in fields:
            if getattr(object, field_name, None) is None:
                raise exc.FieldIsNone(field_name)

    def _assert_forbidden_fields(self, object, fields):
        for field_name in fields:
            if getattr(object, field_name, None) is not None:
                raise exc.ForbiddenField(field=field_name)

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
                    (getattr(object, field_name), )
                )

            if res.fetchone() is not None:
                raise exc.DuplicateObject(field=field_name)

    def _check_foreign_key(self, object, foreign_key, foreign_table):
        cur = self.con.cursor()

        # Since the foreign key exception of sqlite3 has no information
        # which foreign key constrait was breaked, we have to check
        # that by selecting the object.
        c = cur.execute('SELECT 1 FROM {} WHERE id=?;'.format(foreign_table),
                        (getattr(object, foreign_key),))

        if c.fetchone() is None:
            raise exc.ForeignKeyNotExisting(foreign_key)

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
        adminroles = self.getAdminroles(consumer)

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
                raise exc.ConsumerNeedsCredentials()

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
            raise exc.ObjectNotFound
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
                                      ['id', 'date_created'])
        self._check_foreign_key(activity, 'created_by', 'consumers')

        activity.date_created = datetime.datetime.now()
        activity.reviewed = False
        if not (activity.date_created < activity.date_deadline < activity.date_event):
            raise exc.InvalidDates()

        cur.execute('INSERT INTO activities '
                    '(created_by, workactivity_id, '
                    'date_created, date_deadline, date_event, reviewed) '
                    'VALUES(?,?,?,?,?,?);', (
                     activity.created_by, activity.workactivity_id,
                     activity.date_created, activity.date_deadline,
                     activity.date_event, activity.reviewed)
                    )

        self.con.commit()

    def insert_activityfeedback(self, activityfeedback):
        cur = self.con.cursor()

        self._assert_mandatory_fields(activityfeedback,
                                      ['consumer_id',
                                       'activity_id',
                                       'feedback'])
        self._assert_forbidden_fields(activityfeedback, ['id', 'timestamp'])
        self._check_foreign_key(activityfeedback, 'consumer_id', 'consumers')
        self._check_foreign_key(activityfeedback, 'activity_id', 'activities')

        activity = self.get_activity(id=activityfeedback.activity_id)

        activityfeedback.timestamp = datetime.datetime.now()

        if activityfeedback.timestamp > activity.date_deadline:
            raise exc.InvalidDates()

        cur.execute('INSERT INTO activityfeedbacks '
                    '(timestamp, consumer_id, activity_id, feedback) '
                    'VALUES(?,?,?,?);', (
                     activityfeedback.timestamp, activityfeedback.consumer_id,
                     activityfeedback.activity_id, activityfeedback.feedback)
                    )

        self.con.commit()

    def insert_participation(self, participation):
        cur = self.con.cursor()

        self._assert_mandatory_fields(participation,
                                      ['consumer_id',
                                       'activity_id'])
        self._assert_forbidden_fields(participation, ['id', 'timestamp'])
        self._check_foreign_key(participation, 'consumer_id', 'consumers')
        self._check_foreign_key(participation, 'activity_id', 'activities')

        participation.timestamp = datetime.datetime.now()

        cur.execute('INSERT INTO participations '
                    '(timestamp, consumer_id, activity_id) '
                    'VALUES(?,?,?);',
                    (participation.timestamp, participation.consumer_id,
                     participation.activity_id)
                    )

    def insert_product(self, product):
        cur = self.con.cursor()

        self._assert_mandatory_fields(
            product, ['name', 'countable', 'price',
                      'department_id', 'revocable']
        )

        self._assert_forbidden_fields(product, ['id', 'active', 'stock'])
        self._check_uniqueness(product, 'products', ['name'])
        self._check_foreign_key(product, 'department_id', 'departments')

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
            '    departmentpurchase_id, '
            '    comment, '
            '    amount, '
            '    revoked,'
            '    timestamp) '
            'VALUES (?,?,?,?,?,?);',
            (payoff.department_id,
             payoff.departmentpurchase_id,
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
        if self.configuration['USE_KARMA']:
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

    def insert_departmentpurchase(self, dpurchase):
        cur = self.con.cursor()
        self._assert_mandatory_fields(
            dpurchase, ['product_id', 'department_id', 'admin_id',
                        'amount', 'price_per_product'])
        self._assert_forbidden_fields(dpurchase, ['id', 'timestamp'])
        self._check_foreign_key(dpurchase, 'admin_id', 'consumers')
        self._check_foreign_key(dpurchase, 'department_id', 'departments')
        self._check_foreign_key(dpurchase, 'product_id', 'products')

        dpurchase.timestamp = datetime.datetime.now()

        cur.execute('INSERT INTO departmentpurchases '
                    '(timestamp, product_id, department_id, '
                    ' admin_id, amount, price_per_product) '
                    'VALUES (?,?,?,?,?,?);',
                    (dpurchase.timestamp, dpurchase.product_id,
                     dpurchase.department_id, dpurchase.admin_id,
                     dpurchase.amount, dpurchase.price_per_product)
                    )
        dp_id = cur.lastrowid

        cur.execute('UPDATE products SET stock=stock+? WHERE id=?;',
                    (dpurchase.amount, dpurchase.product_id)
                    )

        product = self.get_product(dpurchase.product_id)
        comment = '{}x {}'.format(dpurchase.amount, product.name)
        depositamount = dpurchase.amount * dpurchase.price_per_product
        payoff = models.Payoff(department_id=dpurchase.department_id,
                               comment=comment,
                               amount=depositamount,
                               departmentpurchase_id=dp_id)
        self.insert_payoff(payoff)
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

    def _consumer_credit(self, id):
        _purchases = self.get_purchases_of_consumer(id=id)
        _deposits = self.get_deposits_of_consumer(id=id)

        _purchases = [x for x in _purchases if not x.revoked]

        purchases = list(map(validation.to_dict, _purchases))
        deposits = list(map(validation.to_dict, _deposits))

        d_amount = sum(map(itemgetter('amount'), deposits))
        p_amount = - \
            sum(map(lambda x: x['paid_base_price_per_product']
                    * x['amount'], purchases))
        k_amount = - \
            sum(map(lambda x: x['paid_karma_per_product']
                    * x['amount'], purchases))

        return d_amount + p_amount + k_amount

    def get_activity(self, id):
        return self._get_one(model=models.Activity, id=id)

    def get_workactivity(self, id):
        return self._get_one(model=models.Workactivity, id=id)

    def get_consumer(self, id):
        consumer = self._get_one(model=models.Consumer, id=id)
        consumer.credit = self._consumer_credit(id=consumer.id)
        consumer.isAdmin = len(self.getAdminroles(consumer)) > 0
        consumer.hasCredentials = all([consumer.email, consumer.password])
        return consumer

    def get_product(self, id):
        return self._get_one(model=models.Product, id=id)

    def get_purchase(self, id):
        return self._get_one(model=models.Purchase, id=id)

    def get_departmentpurchase(self, id):
        return self._get_one(model=models.Departmentpurchase, id=id)

    def get_deposit(self, id):
        return self._get_one(model=models.Deposit, id=id)

    def get_department(self, id):
        return self._get_one(model=models.Department, id=id)

    def get_payoff(self, id):
        return self._get_one(model=models.Payoff, id=id)

    def get_bank(self):
        return self._get_one(model=models.Bank, id=1)

    def _get_one(self, model, id):
        cur = self.con.cursor()
        cur.row_factory = factory(model)
        cur.execute('SELECT * FROM {} WHERE id=?;'.format(model._tablename),
                    (id, )
                    )

        res = cur.fetchone()
        if res is None:
            raise exc.ObjectNotFound()
        return res

    def get_consumer_by_email(self, email):
        cur = self.con.cursor()
        cur.row_factory = factory(models.Consumer)
        cur.execute('SELECT * FROM {} WHERE email=?;'.format(
                    models.Consumer._tablename), (email, )
                    )
        res = cur.fetchall()
        if res is None or len(res) > 1:
            raise exc.ObjectNotFound()
        return res[0]

    def get_activityfeedback(self, activity_id, list_all=False):
        consumers = self.list_consumers()

        cur = self.con.cursor()
        cur.row_factory = factory(models.Activityfeedback)

        feedback = {}
        for consumer in consumers:
            feedback[consumer.id] = [] if list_all else None

        if list_all:
            cur.execute('SELECT * FROM {}  WHERE activity_id=?;'.format(
                        models.Activityfeedback._tablename),
                        (activity_id, )
                        )
        else:
            cur.execute('SELECT * FROM activityfeedbacks  WHERE activity_id=? '
                        'GROUP BY consumer_id;'.format(
                         models.Activityfeedback._tablename), (activity_id, )
                        )

        res = cur.fetchall()

        if list_all:
            for r in res:
                feedback[r.consumer_id].append(validation.to_dict(r))

        else:
            for r in res:
                feedback[r.consumer_id] = r.feedback

        return feedback

    def getDepartmentStatistics(self, id):
        statistics = {}
        statistics['department_id'] = id
        statistics['top_products'] = self.get_top_products(department_id=id,
                                                           num_products=10)
        statistics['purchase_times'] = self._get_purchase_times(
          department_id=id)

        return statistics

    def get_top_products(self, department_id, num_products):
        cur = self.con.cursor()
        cur.execute('SELECT product_id, count(product_id) '
                    'FROM {} GROUP BY product_id '
                    'ORDER BY count(product_id) '
                    'DESC LIMIT ?;'.format(models.Purchase._tablename),
                    (num_products,)
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
        return self._get_consumer_data(model=models.Purchase, id=id)

    def get_deposits_of_consumer(self, id):
        return self._get_consumer_data(model=models.Deposit, id=id)

    def _get_consumer_data(self, model, id):
        cur = self.con.cursor()
        cur.row_factory = factory(model)
        cur.execute('SELECT * FROM {} WHERE consumer_id=?;'.format(
                    model._tablename),
                    (id, )
                    )

        return cur.fetchall()

    def get_favorite_products(self, id):
        cur = self.con.cursor()
        cur.row_factory = factory(models.Purchase)
        cur.execute('SELECT * FROM {} WHERE consumer_id=? AND revoked=0 '
                    'GROUP BY product_id ORDER BY COUNT(product_id) DESC '
                    'LIMIT 10;'.format(models.Purchase._tablename), (id,)
                    )
        return cur.fetchall()

    def list_consumers(self):
        _consumers = self._list(model=models.Consumer, limit=None)

        consumers = []

        for consumer in _consumers:
            consumer.credit = self._consumer_credit(id=consumer.id)
            consumers.append(consumer)
            consumer.isAdmin = len(self.getAdminroles(consumer)) > 0
            consumer.hasCredentials = all([consumer.email, consumer.password])

        return consumers

    def list_departmentpurchases(self, department_id):
        cur = self.con.cursor()
        cur.row_factory = factory(models.Departmentpurchase)
        cur.execute('SELECT * FROM {} WHERE department_id={};'.format(
                    models.Departmentpurchase._tablename, department_id)
                    )
        return cur.fetchall()

    def list_products(self):
        return self._list(model=models.Product, limit=None)

    def list_purchases(self, limit=None):
        return self._list(model=models.Purchase, limit=limit)

    def list_deposits(self, limit=None):
        return self._list(model=models.Deposit, limit=limit)

    def list_departments(self):
        return self._list(model=models.Department, limit=None)

    def list_pricecategories(self):
        return self._list(model=models.PriceCategory, limit=None)

    def list_payoffs(self, limit=None):
        return self._list(model=models.Payoff, limit=limit)

    def list_logs(self, limit=None):
        return self._list(model=models.Log, limit=limit)

    def list_workactivities(self):
        return self._list(model=models.Workactivity, limit=None)

    def list_activities(self):
        return self._list(model=models.Activity, limit=None)

    def list_banks(self):
        return self._list(model=models.Bank, limit=None)

    def _list(self, model, limit):
        cur = self.con.cursor()
        cur.row_factory = factory(model)
        if limit is None:
            cur.execute('SELECT * FROM {};'.format(model._tablename))

        else:
            limit = int(limit)
            cur.execute(
                'SELECT * FROM {} ORDER BY id  DESC LIMIT ?;'.format(
                    model._tablename), (limit,)
            )
        return cur.fetchall()

    def _list_purchases_department(self, department_id, limit=None):
        cur = self.con.cursor()
        cur.row_factory = factory(models.Purchase)
        if limit is None:
            cur.execute('SELECT * FROM {} '
                        'WHERE product_id IN (SELECT id FROM products '
                        'WHERE department_id=?) ORDER BY id;'.format(
                         models.Purchase._tablename), (department_id,)
                        )

        else:
            limit = int(limit)
            cur.execute('SELECT * FROM {} WHERE product_id IN '
                        '(SELECT id FROM products WHERE department_id=?) '
                        ' ORDER BY id DESC LIMIT ?;'.format(
                         models.Purchase._tablename),
                        (department_id, limit)
                        )
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

    def update_payoff(self, payoff):
        self._assert_mandatory_fields(payoff, ['id'])
        self._assert_forbidden_fields(
            payoff, ['department_id',
                     'amount']
        )

        if payoff.revoked is None or not payoff.revoked:
            return

        apipayoff = self.get_payoff(payoff.id)
        if apipayoff.revoked:
            raise exc.CanOnlyBeRevokedOnce()

        if payoff.revoked:
            apipayoff.revoked = True

        cur = self.con.cursor()

        # update bank credit
        cur.execute('UPDATE banks SET credit=credit+?;',
                    (apipayoff.amount, ))

        cur.execute('UPDATE departments SET expenses=expenses-? '
                    'WHERE id=?;',
                    (apipayoff.amount, apipayoff.department_id)
                    )

        if apipayoff.departmentpurchase_id:
            dp = self.get_departmentpurchase(id=apipayoff.departmentpurchase_id)
            cur.execute('UPDATE products SET stock=stock-? WHERE id=?;',
                        (dp.amount, dp.department_id)
                        )

        self._simple_update(cur, object=apipayoff, table='payoffs',
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
            raise exc.InvalidDates()

        cur = self.con.cursor()

        self._simple_update(cur, object=activity, table='activities',
                            updateable_fields=['date_deadline', 'date_event'])

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
            raise exc.NotRevocable(product)

        cur = self.con.cursor()

        if purchase.revoked and dbpur.revoked:
            raise exc.CanOnlyBeRevokedOnce()

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
