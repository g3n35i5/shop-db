#!/usr/bin/python3

import datetime
import pdb
import sqlite3
import unittest

import app

from .db_api import *
from .models import (Bank, Consumer, Department, Deposit,
                     Information, Log, Payoff, PriceCategory,
                     Product, Purchase, StockHistory)
from .validation import WrongType

import configuration as config


class TestDatabaseApi(unittest.TestCase):

    def setUpClass():
        # load the db schema
        with open(app.PATH + '/models.sql') as models:
            TestDatabaseApi.schema = models.read()

    def setUp(self):
        # create in memory db and create the tables
        self.con = sqlite3.connect(
            ':memory:', detect_types=sqlite3.PARSE_DECLTYPES)
        self.con.executescript(self.schema)
        configuration = {}
        configuration['USE_KARMA'] = config.BaseConfig.USE_KARMA

        self.api = DatabaseApi(self.con, configuration)

    def tearDown(self):
        # all actions should be committed after the tests
        self.assertFalse(self.con.in_transaction)

    def test_toggle_use_karma(self):
        c = Consumer(name='Hans Müller')
        self.api.insert_consumer(c)

        d = Department(name="Kaffeewart", budget=20000)
        self.api.insert_department(d)

        p = Product(name='Twix', countable=True,
                    price=100, department_id=1, revocable=True)
        self.api.insert_product(p)

        i = self.api.list_information()[0]
        self.assertTrue(i.use_karma)

        pur = Purchase(consumer_id=1, product_id=1, amount=1,
                       comment="bought with karma")

        self.api.insert_purchase(pur)
        c = self.api.get_consumer(id=1)
        self.assertEqual(c.credit, -110)
        purchases = self.api.list_purchases()
        self.assertEqual(len(purchases), 1)
        self.assertEqual(purchases[0].paid_base_price_per_product, 100)
        self.assertEqual(purchases[0].paid_karma_per_product, 10)
        self.assertFalse(purchases[0].revoked)

        # revoke this purchase
        pur = Purchase(id=1, revoked=True)
        self.api.update_purchase(pur)
        purchases = self.api.list_purchases()
        self.assertEqual(len(purchases), 1)
        self.assertEqual(purchases[0].paid_base_price_per_product, 100)
        self.assertEqual(purchases[0].paid_karma_per_product, 10)
        self.assertTrue(purchases[0].revoked)

        c = self.api.get_consumer(id=1)
        self.assertEqual(c.credit, 0)

        i = Information(id=1, use_karma=False)
        self.api.update_information(i)
        i = self.api.list_information()[0]
        self.assertFalse(i.use_karma)

        pur = Purchase(consumer_id=1, product_id=1, amount=1,
                       comment="bought without karma")

        self.api.insert_purchase(pur)
        c = self.api.get_consumer(id=1)
        self.assertEqual(c.credit, -100)
        purchases = self.api.list_purchases()
        self.assertEqual(len(purchases), 2)
        self.assertEqual(purchases[1].paid_base_price_per_product, 100)
        self.assertEqual(purchases[1].paid_karma_per_product, 0)
        self.assertFalse(purchases[1].revoked)

    def test_get_top_products(self):
        c = Consumer(name='Hans Müller')
        self.api.insert_consumer(c)
        d = Department(name="Kaffeewart", budget=20000)
        self.api.insert_department(d)

        p = Product(name='Twix', countable=True,
                    price=100, department_id=1, revocable=True)
        self.api.insert_product(p)
        p = Product(name='Mars', countable=True,
                    price=100, department_id=1, revocable=True)
        self.api.insert_product(p)

        # buy 3x Twix and 1x Snickers
        for i in range(0, 3):
            pur = Purchase(consumer_id=1, product_id=1, amount=1,
                           comment="bought with karma")
            self.api.insert_purchase(pur)
        for i in range(0, 2):
            pur = Purchase(consumer_id=1, product_id=2, amount=1,
                           comment="bought with karma")
            self.api.insert_purchase(pur)

        top = self.api.get_top_products(2)
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0][0], 1)
        self.assertEqual(top[0][1], 3)
        self.assertEqual(top[1][0], 2)
        self.assertEqual(top[1][1], 2)

    def test_insert_consumer(self):
        # insert correctly
        c = Consumer(name='Hans Müller')
        self.api.insert_consumer(c)
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.name, 'Hans Müller')
        self.assertEqual(consumer.credit, 0)
        self.assertEqual(consumer.karma, 0)
        self.assertTrue(consumer.active)

        # missing fields
        with self.assertRaises(FieldIsNone):
            c = Consumer()
            self.api.insert_consumer(c)

        # insert wrong types
        with self.assertRaises(WrongType):
            c = Consumer(name=2)

        # id should be forbidden
        c = Consumer(id=13, name='Hans')
        with self.assertRaises(ForbiddenField):
            self.api.insert_consumer(c)

        # credit should be forbidden
        c = Consumer(name='Hans', credit=12)
        with self.assertRaises(ForbiddenField):
            self.api.insert_consumer(c)

        # duplicate names should be rejected
        c = Consumer(name='Hans Müller')
        with self.assertRaises(DuplicateObject):
            self.api.insert_consumer(c)

    def test_adminroles(self):
        consumer = Consumer(name='Hans Müller')
        self.api.insert_consumer(consumer)
        consumer = self.api.get_consumer(id=1)

        department = Department(name="Kaffeewart", budget=20000)
        self.api.insert_department(department)
        department = self.api.get_department(id=1)

        # Make sure, that the consumer is no admin
        adminroles = self.api.getAdminroles(consumer)
        self.assertEqual(len(adminroles), 0)

        # Make sure, that the consumer needs email and password to be admin
        with self.assertRaises(ConsumerNeedsCredentials):
                self.api.toggleAdmin(consumer, department)

        # Update the consumer, so he can be admin
        upConsumer = Consumer(id=consumer.id)
        upConsumer.email = 'me@example.com'
        upConsumer.password = 'supersecretpassword'.encode()

        self.api.update_consumer(upConsumer)
        consumer = self.api.get_consumer(id=1)

        # Make consumer admin for department 1
        self.api.toggleAdmin(consumer, department)
        adminroles = self.api.getAdminroles(consumer)
        self.assertEqual(adminroles[0].department_id, 1)
        self.assertEqual(len(adminroles), 1)

        # Delete consumer admin role for department 1
        self.api.toggleAdmin(consumer, department)
        adminroles = self.api.getAdminroles(consumer)
        self.assertEqual(len(adminroles), 0)




    def test_insert_department(self):
        d = Department(name="Kaffeewart", budget=20000)
        self.api.insert_department(d)
        d = Department(name="Pizzawart", budget=30000)
        self.api.insert_department(d)
        d = Department(name="Getränkewart", budget=40000)
        self.api.insert_department(d)

        departments = self.api.list_departments()
        self.assertEqual(len(departments), 3)

        # check id's
        self.assertEqual(departments[0].id, 1)
        self.assertEqual(departments[1].id, 2)
        self.assertEqual(departments[2].id, 3)

        # check names
        self.assertEqual(departments[0].name, "Kaffeewart")
        self.assertEqual(departments[1].name, "Pizzawart")
        self.assertEqual(departments[2].name, "Getränkewart")

        # check incomes
        self.assertEqual(departments[0].income_base, 0)
        self.assertEqual(departments[1].income_base, 0)
        self.assertEqual(departments[2].income_base, 0)

        self.assertEqual(departments[0].income_karma, 0)
        self.assertEqual(departments[1].income_karma, 0)
        self.assertEqual(departments[2].income_karma, 0)

        # check expenses
        self.assertEqual(departments[0].expenses, 0)
        self.assertEqual(departments[1].expenses, 0)
        self.assertEqual(departments[2].expenses, 0)

        # check expenses
        self.assertEqual(departments[0].budget, 20000)
        self.assertEqual(departments[1].budget, 30000)
        self.assertEqual(departments[2].budget, 40000)

    def test_insert_product(self):
        # insert correctly
        d = Department(name="Kaffeewart", budget=20000)
        self.api.insert_department(d)

        p = Product(name='Twix', countable=True, price=90,
                    department_id=1, revocable=True)
        self.api.insert_product(p)
        product = self.api.get_product(id=1)
        self.assertEqual(product.name, 'Twix')
        self.assertEqual(product.price, 90)
        self.assertEqual(product.department_id, 1)
        self.assertTrue(product.active)
        self.assertEqual(product.stock, 0)

        # missing fields
        with self.assertRaises(FieldIsNone):
            p = Product(name='Twix', price=250)
            self.api.insert_product(p)

        # insert wrong types
        with self.assertRaises(WrongType):
            p = Product(name=2, countable=True,
                        price=100, department_id=1, revocable=True)

        # product.id should be forbidden
        p = Product(id=10, name='Twix', countable=True,
                    price=100, department_id=1, revocable=True)
        with self.assertRaises(ForbiddenField):
            self.api.insert_product(p)

        # duplicate names should be rejected
        p = Product(name='Twix', countable=True,
                    price=100, department_id=1, revocable=True)
        with self.assertRaises(DuplicateObject):
            self.api.insert_product(p)

    def test_update_consumer(self):
        c = Consumer(name='Hans Müller')
        self.api.insert_consumer(c)
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.name, 'Hans Müller')
        self.assertEqual(consumer.karma, 0)
        consumer = Consumer(id=1, name='Peter Meier')
        self.api.update_consumer(consumer)
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.name, 'Peter Meier')
        consumer = Consumer(id=1, karma=10)
        self.api.update_consumer(consumer)
        karmahistory = self.api.get_karma_history(id=1)
        self.assertEqual(len(karmahistory), 1)
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.karma, 10)

        # test karmahistory
        consumer = Consumer(id=1, karma=9)
        self.api.update_consumer(consumer)
        karmahistory = self.api.get_karma_history(id=1)
        self.assertEqual(len(karmahistory), 2)

        consumer = Consumer(id=1, karma=8)
        self.api.update_consumer(consumer)
        karmahistory = self.api.get_karma_history(id=1)
        self.assertEqual(len(karmahistory), 3)

        consumer = Consumer(id=1, karma=7)
        self.api.update_consumer(consumer)
        karmahistory = self.api.get_karma_history(id=1)
        self.assertEqual(len(karmahistory), 4)

        self.assertEqual(karmahistory[0].data_inserted, 'karma=7')
        self.assertEqual(karmahistory[1].data_inserted, 'karma=8')
        self.assertEqual(karmahistory[2].data_inserted, 'karma=9')
        self.assertEqual(karmahistory[3].data_inserted, 'karma=10')

        c = Consumer(id=1, credit=1337)
        with self.assertRaises(ForbiddenField):
            self.api.update_consumer(c)
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, 0)

        c = Consumer(active=False)
        with self.assertRaises(FieldIsNone):
            self.api.update_consumer(c)

    def test_get_product_by_id(self):
        d = Department(name="Kaffeewart", budget=20000)
        self.api.insert_department(d)

        p = Product(name='Twix', countable=True,
                    price=90, department_id=1, revocable=True)
        self.api.insert_product(p)
        product = self.api.get_product(id=1)
        self.assertEqual(product.name, 'Twix')
        self.assertEqual(product.price, 90)
        self.assertEqual(product.department_id, 1)
        self.assertTrue(product.active)
        self.assertEqual(product.stock, 0)

    def test_get_products(self):
        d = Department(name="Kaffeewart", budget=20000)
        self.api.insert_department(d)
        d = Department(name="Pizzawart", budget=20000)
        self.api.insert_department(d)

        p1 = Product(name='Mars', countable=True,
                     price=30, department_id=1, revocable=True)
        p2 = Product(name='Twix', countable=True,
                     price=40, department_id=2, revocable=True)
        self.api.insert_product(p1)
        self.api.insert_product(p2)

        products = self.api.list_products()
        self.assertIs(type(products), list)
        self.assertEqual(len(products), 2)
        # Mars
        self.assertEqual(products[0].name, 'Mars')
        self.assertEqual(products[0].price, 30)
        self.assertEqual(products[0].department_id, 1)
        self.assertTrue(products[0].active)
        self.assertEqual(products[0].stock, 0)
        # Twix
        self.assertEqual(products[1].name, 'Twix')
        self.assertEqual(products[1].price, 40)
        self.assertEqual(products[1].department_id, 2)
        self.assertTrue(products[1].active)
        self.assertEqual(products[1].stock, 0)

    def test_create_payoff(self):
        d = Department(name="Kaffeewart", budget=20000)
        self.api.insert_department(d)
        department = self.api.get_department(id=1)
        self.assertEqual(department.expenses, 0)
        bank = self.api.get_bank()
        self.assertEqual(bank.credit, 0)

        p = Payoff(department_id=1, amount=2000, comment="payoff test")
        self.api.insert_payoff(p)
        bank = self.api.get_bank()
        self.assertEqual(bank.credit, -2000)
        department = self.api.get_department(id=1)
        self.assertEqual(department.expenses, 2000)

        # revoke payoff
        p = Payoff(id=1, revoked=True)
        self.api.update_payoff(p)

        bank = self.api.get_bank()
        self.assertEqual(bank.credit, 0)
        department = self.api.get_department(id=1)
        self.assertEqual(department.expenses, 0)

    def test_create_deposit(self):
        # create test consumer
        c = Consumer(name='Hans Müller')
        self.api.insert_consumer(c)

        # check the consumers credit
        consumer = self.api.get_consumer(1)
        self.assertEqual(consumer.credit, 0)

        # create deposit
        dep1 = Deposit(consumer_id=1, amount=250, comment="testcomment")
        self.api.insert_deposit(dep1)

        # check, if the consumers credit has been increased
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, 250)

        # check the results
        deposit = self.api.get_deposit(id=1)
        self.assertEqual(deposit.amount, 250)
        self.assertEqual(deposit.comment, "testcomment")
        self.assertEqual(deposit.consumer_id, consumer.id)

        # test with wrong foreign_key consumer_id
        dep2 = Deposit(consumer_id=2, amount=240, comment="testcomment")
        with self.assertRaises(ForeignKeyNotExisting):
            self.api.insert_deposit(dep2)

        # deposit.id should be forbidden
        dep3 = Deposit(consumer_id=2, amount=20, id=12, comment="testcomment")
        with self.assertRaises(ForbiddenField):
            self.api.insert_deposit(dep3)

        # deposit.timestamp should be forbidden
        dep4 = Deposit(consumer_id=2, amount=20, comment="testcomment",
                       timestamp=datetime.datetime.now())
        with self.assertRaises(ForbiddenField):
            self.api.insert_deposit(dep3)

    def test_stockhistory(self):
        d = Department(name="Kaffeewart", budget=20000)
        self.api.insert_department(d)

        p1 = Product(name='Coffee', countable=True,
                    price=100, department_id=1, revocable=True)

        p2 = Product(name='Mars', countable=False,
                    price=100, department_id=1, revocable=True)

        c = Consumer(name='Karl')
        self.api.insert_product(p1)
        self.api.insert_product(p2)

        self.api.insert_consumer(c)

        sh = self.api.get_stockhistory(product_id=1)
        self.assertEqual(len(sh), 0)

        for i in range(1, 10):
            p1 = Purchase(consumer_id=1, product_id=1,
                          amount=1, comment="purchase")

            p2 = Purchase(consumer_id=1, product_id=2,
                          amount=1, comment="purchase")
            self.api.insert_purchase(p1)
            self.api.insert_purchase(p2)

            # check countable product
            sh = self.api.get_stockhistory(product_id=1)
            self.assertEqual(len(sh), i)
            self.assertEqual(sh[i - 1].new_stock, -i)

            # check non countable product
            with self.assertRaises(ProductNotCountable):
                sh = self.api.get_stockhistory(product_id=2)

        # check select timestamps
        # check without given range of time
        sh = self.api.get_stockhistory(product_id=1)
        self.assertEqual(len(sh), 9)

        # check with given range of time
        date_start = datetime.datetime.now()
        date_end = datetime.datetime.now() + datetime.timedelta(minutes=1)

        sh = self.api.get_stockhistory(product_id=1,
                                       date_start=date_start,
                                       date_end=date_end)

        self.assertEqual(len(sh), 0)




    def test_insert_purchase(self):
        d = Department(name="Kaffeewart", budget=20000)
        self.api.insert_department(d)

        department = self.api.get_department(id=1)
        self.assertEqual(department.id, 1)
        self.assertEqual(department.name, "Kaffeewart")
        self.assertEqual(department.income_base, 0)
        self.assertEqual(department.income_karma, 0)
        self.assertEqual(department.expenses, 0)
        self.assertEqual(department.budget, 20000)

        # insert consumer and product
        p = Product(name='Coffee', countable=True,
                    price=100, department_id=1, revocable=True)
        c1 = Consumer(name='Dude')
        c2 = Consumer(name='Awesome Dude')
        c3 = Consumer(name='Bad Dude')
        self.api.insert_product(p)

        self.api.insert_consumer(c1)
        self.api.insert_consumer(c2)
        self.api.insert_consumer(c3)

        c2 = Consumer(id=2, karma=10)
        c3 = Consumer(id=3, karma=-10)

        self.api.update_consumer(c2)
        self.api.update_consumer(c3)

        # check consumers
        consumers = self.api.list_consumers()
        self.assertEqual(len(consumers), 3)
        self.assertEqual(consumers[0].credit, 0)
        self.assertEqual(consumers[1].credit, 0)
        self.assertEqual(consumers[2].credit, 0)

        self.assertEqual(consumers[0].karma, 0)
        self.assertEqual(consumers[1].karma, 10)
        self.assertEqual(consumers[2].karma, -10)

        # check, if the objects are correct
        product = self.api.get_product(id=1)
        self.assertEqual(product.price, 100)

        pur1 = Purchase(consumer_id=1, product_id=1, amount=1,
                        comment="good dude buys something")

        pur2 = Purchase(consumer_id=2, product_id=1, amount=1,
                        comment="awesome dude buys something")

        pur3 = Purchase(consumer_id=3, product_id=1, amount=1,
                        comment="bad dude buys something")

        self.api.insert_purchase(pur1)
        self.api.insert_purchase(pur2)
        self.api.insert_purchase(pur3)

        # get purchases
        purchases = self.api.list_purchases()
        self.assertEqual(len(purchases), 3)

        self.assertEqual(purchases[0].paid_base_price_per_product, 100)
        self.assertEqual(purchases[0].paid_karma_per_product, 10)
        self.assertEqual(purchases[0].amount, 1)
        self.assertEqual(purchases[0].comment, "good dude buys something")
        self.assertIsNotNone(purchases[0].timestamp)

        self.assertEqual(purchases[1].paid_base_price_per_product, 100)
        self.assertEqual(purchases[1].paid_karma_per_product, 0)
        self.assertEqual(purchases[1].amount, 1)
        self.assertEqual(purchases[1].comment, "awesome dude buys something")
        self.assertIsNotNone(purchases[1].timestamp)

        self.assertEqual(purchases[2].paid_base_price_per_product, 100)
        self.assertEqual(purchases[2].paid_karma_per_product, 20)
        self.assertEqual(purchases[2].amount, 1)
        self.assertEqual(purchases[2].comment, "bad dude buys something")
        self.assertIsNotNone(purchases[2].timestamp)

        # check consumers
        consumers = self.api.list_consumers()
        self.assertEqual(len(consumers), 3)
        self.assertEqual(consumers[0].credit, -110)
        self.assertEqual(consumers[1].credit, -100)
        self.assertEqual(consumers[2].credit, -120)

        department = self.api.get_department(id=1)
        self.assertEqual(department.id, 1)
        self.assertEqual(department.name, "Kaffeewart")
        self.assertEqual(department.income_base, 300)
        self.assertEqual(department.income_karma, 30)
        self.assertEqual(department.expenses, 0)
        self.assertEqual(department.budget, 20000)

        # now we revoke the purchases
        pur = Purchase(id=1, revoked=True)
        self.api.update_purchase(pur)
        department = self.api.get_department(id=1)
        self.assertEqual(department.income_base, 200)
        self.assertEqual(department.income_karma, 20)

        pur = Purchase(id=2, revoked=True)
        self.api.update_purchase(pur)
        department = self.api.get_department(id=1)
        self.assertEqual(department.income_base, 100)
        self.assertEqual(department.income_karma, 20)

        pur = Purchase(id=3, revoked=True)
        self.api.update_purchase(pur)
        department = self.api.get_department(id=1)
        self.assertEqual(department.income_base, 0)
        self.assertEqual(department.income_karma, 0)

        # test with wrong foreign key consumer_id
        pur4 = Purchase(consumer_id=4, product_id=1, amount=1,
                        comment="purchase done by unittest")
        with self.assertRaises(ForeignKeyNotExisting):
            self.api.insert_purchase(pur4)

        # no new purchase should have been created
        self.assertEqual(len(self.api.list_purchases()), 3)

        # test with wrong foreign key product_id
        pur5 = Purchase(consumer_id=1, product_id=2, amount=1,
                        comment="purchase done by unittest")
        with self.assertRaises(ForeignKeyNotExisting):
            self.api.insert_purchase(pur5)

        # no new purchase should have been created
        self.assertEqual(len(self.api.list_purchases()), 3)

        # the credit of the consumer must not have to be changed
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, 0)

        # purchase.id should be forbidden
        pur6 = Purchase(consumer_id=1, product_id=1, id=1337, amount=1,
                        comment="purchase done by unittest")
        with self.assertRaises(ForbiddenField):
            self.api.insert_purchase(pur6)

        # purchase.paid_base_price_per_product and paid_karma_per_product
        # should be forbidden
        pur7 = Purchase(consumer_id=1, product_id=1,
                        paid_base_price_per_product=200,
                        paid_karma_per_product=200,
                        amount=1,
                        comment="purchase done by unittest")
        with self.assertRaises(ForbiddenField):
            self.api.insert_purchase(pur7)

        # purchase.revoked should be forbidden
        pur8 = Purchase(consumer_id=1, product_id=1, revoked=True, amount=1,
                        comment="purchase done by unittest")
        with self.assertRaises(ForbiddenField):
            self.api.insert_purchase(pur8)

        # purchase.revoked should be forbidden
        pur9 = Purchase(consumer_id=1, product_id=1, amount=1,
                        timestamp=datetime.datetime.now(),
                        comment="purchase done by unittest")
        with self.assertRaises(ForbiddenField):
            self.api.insert_purchase(pur9)

    def test_inventory_system(self):
        d = Department(name="Kaffeewart", budget=20000)
        self.api.insert_department(d)

        # insert consumer and product
        p = Product(name='Mars', countable=True,
                    price=20, department_id=1, revocable=True)
        c = Consumer(name='Hans Müller')
        self.api.insert_product(p)
        self.api.insert_consumer(c)

        p = Product(id=1, stock=10)
        self.api.update_product(p)

        p = self.api.get_product(id=1)
        self.assertEqual(p.stock, 10)
        self.assertTrue(p.countable)

        for i in range(1, 6):
            pur = Purchase(consumer_id=1, product_id=1,
                           amount=2, comment='testing inventory')
            self.api.insert_purchase(pur)

        p = self.api.get_product(id=1)
        self.assertEqual(p.stock, 0)

        for i in range(1, 3):
            pur = Purchase(id=i, revoked=True, comment='revoking purchase')
            self.api.update_purchase(pur)

        p = self.api.get_product(id=1)
        self.assertEqual(p.stock, 4)

        # check non countable products
        p = Product(name='Coffee', countable=False,
                    price=20, department_id=1, revocable=True)

        self.api.insert_product(p)
        p = self.api.get_product(id=2)
        self.assertFalse(p.countable)
        self.assertEqual(p.stock, None)

        pur = Purchase(consumer_id=1, product_id=2,
                       amount=5, comment='testing inventory')

        p = self.api.get_product(id=2)
        self.assertEqual(p.stock, None)

    def test_limit_list_purchases(self):
        d = Department(name="Kaffeewart", budget=20000)
        self.api.insert_department(d)

        # insert consumer and product
        p = Product(name='Coffee', countable=True,
                    price=20, department_id=1, revocable=True)
        c = Consumer(name='Hans Müller')
        self.api.insert_product(p)
        self.api.insert_consumer(c)

        # check, if the objects are correct
        consumer = self.api.get_consumer(id=1)
        product = self.api.get_product(id=1)
        self.assertEqual(consumer.credit, 0)
        self.assertEqual(product.price, 20)

        pur = Purchase(consumer_id=1, product_id=1, amount=1,
                       comment="purchase done by unittest")
        self.api.insert_purchase(pur)
        pur = Purchase(consumer_id=1, product_id=1, amount=2,
                       comment="purchase done by unittest")
        self.api.insert_purchase(pur)
        pur = Purchase(consumer_id=1, product_id=1, amount=3,
                       comment="purchase done by unittest")
        self.api.insert_purchase(pur)
        pur = Purchase(consumer_id=1, product_id=1, amount=4,
                       comment="purchase done by unittest")
        self.api.insert_purchase(pur)

        # get all purchases
        purchases = self.api.list_purchases()
        self.assertEqual(len(purchases), 4)
        self.assertEqual(purchases[0].amount, 1)
        self.assertEqual(purchases[1].amount, 2)
        self.assertEqual(purchases[2].amount, 3)
        self.assertEqual(purchases[3].amount, 4)

        # get purchases with limit
        purchases = self.api.list_purchases(limit=2)
        self.assertEqual(len(purchases), 2)
        self.assertEqual(purchases[0].amount, 4)
        self.assertEqual(purchases[1].amount, 3)

    def test_update_purchase(self):
        d = Department(name="Kaffeewart", budget=20000)
        self.api.insert_department(d)

        # insert consumer and product
        p = Product(name='Coffee', countable=True,
                    price=20, department_id=1, revocable=True)
        c1 = Consumer(name='Hans Müller')
        self.api.insert_product(p)
        self.api.insert_consumer(c1)

        # check, if the objects are correct
        consumer = self.api.get_consumer(id=1)
        product = self.api.get_product(id=1)
        self.assertEqual(consumer.credit, 0)
        self.assertEqual(product.price, 20)

        pur = Purchase(consumer_id=1, product_id=1, amount=5,
                       comment="purchase done by unittest")
        self.api.insert_purchase(pur)

        # check if the consumers credit has decreased
        pur = self.api.get_purchase(id=1)
        self.assertEqual(pur.comment, "purchase done by unittest")
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit,
                         0 - pur.amount * pur.paid_base_price_per_product
                         - pur.amount * pur.paid_karma_per_product)

        # revoke purchase and update comment
        pur = Purchase(id=1, revoked=True,
                       comment="purchases updated with unittest")
        self.api.update_purchase(pur)

        # check if the purchase has been updated
        pur2 = self.api.get_purchase(id=1)
        self.assertEqual(pur2.comment, "purchases updated with unittest")
        self.assertTrue(pur2.revoked)

        # do it twice to check whether it's indeponent
        with self.assertRaises(CanOnlyBeRevokedOnce):
            self.api.update_purchase(pur)

        # check if the consumers credit has increased
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, 0)

        # this should do nothing
        pur = Purchase(id=1)
        self.api.update_purchase(pur)

        # check if the consumers credit is the same
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, 0)

        # check non revocable products
        p = Product(name='Drucken', countable=False,
                    price=1, department_id=1, revocable=False)

        self.api.insert_product(p)

        pur = Purchase(consumer_id=1, product_id=2, amount=5,
                       comment="purchase done by unittest")
        self.api.insert_purchase(pur)

        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, -5)

        # revoke purchase and update comment
        pur = Purchase(id=2, revoked=True, comment="this should fail")
        with self.assertRaises(NotRevocable):
            self.api.update_purchase(pur)

        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, -5)

    def test_update_product(self):
        d = Department(name="Kaffeewart", budget=20000)
        self.api.insert_department(d)
        d = Department(name="Pizzawart", budget=20000)
        self.api.insert_department(d)

        # create test products
        prod1 = Product(name='Twix', countable=True,
                        price=90, department_id=1, revocable=True)
        self.api.insert_product(prod1)
        prod2 = Product(name='Bounty', countable=True,
                        price=80, department_id=1, revocable=True)
        self.api.insert_product(prod2)

        # define a shortcut to test the state of the product with id=1
        def check_product(name, price, active, stock, department_id):
            # check whether the product was inserted correctly
            prod = self.api.get_product(id=1)
            self.assertEqual(prod.name, name)
            self.assertEqual(prod.price, price)
            self.assertEqual(prod.active, active)
            self.assertEqual(prod.stock, stock)
            self.assertEqual(prod.department_id, department_id)

        # test update name
        prod3 = Product(id=1, name='Mars')
        self.api.update_product(prod3)
        check_product('Mars', 90, True, 0, 1)

        # test update active and stock
        prod4 = Product(id=1, active=False, stock=10)
        self.api.update_product(prod4)
        check_product('Mars', 90, False, 10, 1)

        # test update department_id
        prod4 = Product(id=1, department_id=2)
        self.api.update_product(prod4)
        check_product('Mars', 90, False, 10, 2)

        # test update price (negative prices are allowed!)
        prod5 = Product(id=1, price=-10)
        self.api.update_product(prod5)
        check_product('Mars', -10, False, 10, 2)

        # test update without id
        prod6 = Product(name="Rafaelo")
        with self.assertRaises(FieldIsNone):
            self.api.update_product(prod6)
        # this should still be the same as before
        check_product('Mars', -10, False, 10, 2)

        # test update with unknown id
        prod7 = Product(id=3, name="Rafaelo")
        with self.assertRaises(ObjectNotFound):
            self.api.update_product(prod7)
        # this should still be the same as before
        check_product('Mars', -10, False, 10, 2)

        # test update with duplicate name
        prod8 = Product(id=1, name="Bounty")
        with self.assertRaises(DuplicateObject):
            self.api.update_product(prod8)
        # this should still be the same as before
        check_product('Mars', -10, False, 10, 2)
