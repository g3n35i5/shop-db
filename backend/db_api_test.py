import datetime
import pdb
import sqlite3
import unittest

import app

from .db_api import *
from .models import (Bank, Consumer, Deed, Department, Deposit, Flag, Log,
                     Participation, Payoff, Product, Purchase)
from .validation import WrongType


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

        self.api = DatabaseApi(self.con)

    def tearDown(self):
        # all actions should be committed after the tests
        self.assertFalse(self.con.in_transaction)

    def test_insert_consumer(self):
        # insert correctly
        c = Consumer(name='Hans Müller', active=True, credit=250, karma=0)
        self.api.insert_consumer(c)
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.name, 'Hans Müller')
        self.assertEqual(consumer.credit, 250)
        self.assertEqual(consumer.karma, 0)
        self.assertTrue(consumer.active)

        # missing fields
        with self.assertRaises(FieldIsNone):
            c = Consumer(name='Hans Müller', credit=250)
            self.api.insert_consumer(c)

        # insert wrong types
        with self.assertRaises(WrongType):
            c = Consumer(name=2, active=True, credit=250, karma=0)

        # id should be forbidden
        c = Consumer(id=13, name='Hans', credit=12, active=True, karma=0)
        with self.assertRaises(ForbiddenField):
            self.api.insert_consumer(c)

        # duplicate names should be rejected
        c = Consumer(name='Hans Müller', active=True, credit=0, karma=0)
        with self.assertRaises(DuplicateObject):
            self.api.insert_consumer(c)

    def test_insert_deed(self):
        d = Deed(name="Getränke tragen",
                 timestamp=datetime.datetime.now(), done=False)

        self.api.insert_deed(d)
        deed = self.api.get_deed(id=1)
        self.assertEqual(deed.name, "Getränke tragen")
        self.assertEqual(deed.done, 0)
        self.assertIsNotNone(deed.timestamp)

    def test_insert_participation(self):
        c = Consumer(name='Hans Müller', active=True, credit=250, karma=0)
        self.api.insert_consumer(c)

        f = Flag(name="Teilgenommen")
        self.api.insert_flag(f)

        d = Deed(name="Getränke tragen",
                 timestamp=datetime.datetime.now(), done=False)
        self.api.insert_deed(d)
        deed = self.api.get_deed(id=1)
        self.assertEqual(deed.name, "Getränke tragen")
        self.assertEqual(deed.done, 0)
        self.assertIsNotNone(deed.timestamp)

        p = Participation(consumer_id=1, deed_id=1,
                          timestamp=datetime.datetime.now(), flag_id=1)

        self.api.insert_participation(p)
        participations = self.api.list_participations()
        self.assertEqual(len(participations), 1)

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

        p = Product(name='Twix', active=True, on_stock=True,
                    price=90, department_id=1, revocable=True)
        self.api.insert_product(p)
        product = self.api.get_product(id=1)
        self.assertEqual(product.name, 'Twix')
        self.assertEqual(product.price, 90)
        self.assertEqual(product.department_id, 1)
        self.assertTrue(product.active)
        self.assertTrue(product.on_stock)

        # missing fields
        with self.assertRaises(FieldIsNone):
            p = Product(name='Twix', price=250)
            self.api.insert_product(p)

        # insert wrong types
        with self.assertRaises(WrongType):
            p = Product(name=2, active=True, price=250,
                        department_id=1, revocable=True)

        # product.id should be forbidden
        p = Product(id=1337, name="Mars", active=True, price=250,
                    on_stock=True, department_id=1, revocable=True)
        with self.assertRaises(ForbiddenField):
            self.api.insert_product(p)

        # duplicate names should be rejected
        c = Product(name='Twix', active=False,
                    on_stock=False, price=30, department_id=1, revocable=True)
        with self.assertRaises(DuplicateObject):
            self.api.insert_product(c)

    def test_update_consumer(self):
        c = Consumer(name='Hans Müller', active=True, credit=250, karma=0)
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
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.karma, 10)

        c = Consumer(id=1, credit=1337)
        with self.assertRaises(ForbiddenField):
            self.api.update_consumer(c)
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, 250)

        c = Consumer(active=False)
        with self.assertRaises(FieldIsNone):
            self.api.update_consumer(c)

    def test_get_product_by_id(self):
        d = Department(name="Kaffeewart", budget=20000)
        self.api.insert_department(d)

        p = Product(name='Twix', active=True, on_stock=True,
                    price=90, department_id=1, revocable=True)
        self.api.insert_product(p)
        product = self.api.get_product(id=1)
        self.assertEqual(product.name, 'Twix')
        self.assertEqual(product.price, 90)
        self.assertEqual(product.department_id, 1)
        self.assertTrue(product.active)
        self.assertTrue(product.on_stock)

    def test_get_products(self):
        d = Department(name="Kaffeewart", budget=20000)
        self.api.insert_department(d)
        d = Department(name="Pizzawart", budget=20000)
        self.api.insert_department(d)

        p1 = Product(name='Mars', price=30, active=True,
                     on_stock=False, department_id=1, revocable=True)
        p2 = Product(name='Twix', price=40, active=False,
                     on_stock=True, department_id=2, revocable=True)
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
        self.assertFalse(products[0].on_stock)
        # Twix
        self.assertEqual(products[1].name, 'Twix')
        self.assertEqual(products[1].price, 40)
        self.assertEqual(products[1].department_id, 2)
        self.assertFalse(products[1].active)
        self.assertTrue(products[1].on_stock)

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
        c = Consumer(name='Hans Müller', active=True, credit=250, karma=0)
        self.api.insert_consumer(c)

        # check the consumers credit
        consumer = self.api.get_consumer(1)
        self.assertEqual(consumer.credit, 250)

        # create deposit
        dep1 = Deposit(consumer_id=1, amount=250, comment="testcomment")
        self.api.insert_deposit(dep1)

        # check, if the consumers credit has been increased
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, 500)

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
        p = Product(name='Coffee', price=100, active=True,
                    on_stock=True, department_id=1, revocable=True)
        c1 = Consumer(name='Dude', active=True, credit=250, karma=0)
        c2 = Consumer(name='Awesome Dude', active=True, credit=250, karma=10)
        c3 = Consumer(name='Bad Dude', active=True, credit=250, karma=-10)
        self.api.insert_product(p)

        self.api.insert_consumer(c1)
        self.api.insert_consumer(c2)
        self.api.insert_consumer(c3)

        # check consumers
        consumers = self.api.list_consumers()
        self.assertEqual(len(consumers), 3)
        self.assertEqual(consumers[0].credit, 250)
        self.assertEqual(consumers[1].credit, 250)
        self.assertEqual(consumers[2].credit, 250)

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
        self.assertEqual(consumers[0].credit, 140)
        self.assertEqual(consumers[1].credit, 150)
        self.assertEqual(consumers[2].credit, 130)

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
        self.assertEqual(consumer.credit, 250)

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

    def test_limit_list_purchases(self):
        d = Department(name="Kaffeewart", budget=20000)
        self.api.insert_department(d)

        # insert consumer and product
        p = Product(name='Coffee', price=20, active=True,
                    on_stock=True, department_id=1, revocable=True)
        c = Consumer(name='Hans Müller', active=True, credit=250, karma=0)
        self.api.insert_product(p)
        self.api.insert_consumer(c)

        # check, if the objects are correct
        consumer = self.api.get_consumer(id=1)
        product = self.api.get_product(id=1)
        self.assertEqual(consumer.credit, 250)
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
        p = Product(name='Coffee', price=20, active=True,
                    on_stock=True, department_id=1, revocable=True)
        c1 = Consumer(name='Hans Müller', active=True, credit=250, karma=0)
        self.api.insert_product(p)
        self.api.insert_consumer(c1)

        # check, if the objects are correct
        consumer = self.api.get_consumer(id=1)
        product = self.api.get_product(id=1)
        self.assertEqual(consumer.credit, 250)
        self.assertEqual(product.price, 20)

        pur = Purchase(consumer_id=1, product_id=1, amount=5,
                       comment="purchase done by unittest")
        self.api.insert_purchase(pur)

        # check if the consumers credit has decreased
        pur = self.api.get_purchase(id=1)
        self.assertEqual(pur.comment, "purchase done by unittest")
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit,
                         250 - pur.amount * pur.paid_base_price_per_product
                         - pur.amount * pur.paid_karma_per_product)

        # revoke purchase and update comment
        pur = Purchase(id=1, revoked=True,
                       comment="purchases updated with unittest")
        self.api.update_purchase(pur)
        # do it twice to check whether it's indeponent
        with self.assertRaises(CanOnlyBeRevokedOnce):
            self.api.update_purchase(pur)

        # check if the purchase has been updated
        pur2 = self.api.get_purchase(id=1)
        self.assertEqual(pur2.comment, "purchases updated with unittest")
        self.assertTrue(pur2.revoked)

        # check if the consumers credit has increased
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, 250)

        # this should do nothing
        pur = Purchase(id=1)
        self.api.update_purchase(pur)

        # check if the consumers credit is the same
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, 250)

        # check non revocable products
        p = Product(name='Drucken', price=1, active=True,
                    on_stock=True, department_id=1, revocable=False)

        self.api.insert_product(p)

        pur = Purchase(consumer_id=1, product_id=2, amount=5,
                       comment="purchase done by unittest")
        self.api.insert_purchase(pur)

        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, 245)

        # revoke purchase and update comment
        pur = Purchase(id=2, revoked=True, comment="this should fail")
        with self.assertRaises(NotRevocable):
            self.api.update_purchase(pur)

        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, 245)

    def test_update_product(self):
        d = Department(name="Kaffeewart", budget=20000)
        self.api.insert_department(d)
        d = Department(name="Pizzawart", budget=20000)
        self.api.insert_department(d)

        # create test products
        prod1 = Product(name='Twix', active=True,
                        on_stock=True, price=90, department_id=1, revocable=True)
        self.api.insert_product(prod1)
        prod2 = Product(name='Bounty', active=True,
                        on_stock=False, price=80, department_id=1, revocable=True)
        self.api.insert_product(prod2)

        # define a shortcut to test the state of the product with id=1
        def check_product(name, price, active, on_stock, department_id):
            # check whether the product was inserted correctly
            prod = self.api.get_product(id=1)
            self.assertEqual(prod.name, name)
            self.assertEqual(prod.price, price)
            self.assertEqual(prod.active, active)
            self.assertEqual(prod.on_stock, on_stock)
            self.assertEqual(prod.department_id, department_id)

        # test update name
        prod3 = Product(id=1, name='Mars')
        self.api.update_product(prod3)
        check_product('Mars', 90, True, True, 1)

        # test update active and on_stock
        prod4 = Product(id=1, active=False, on_stock=False)
        self.api.update_product(prod4)
        check_product('Mars', 90, False, False, 1)

        # test update department_id
        prod4 = Product(id=1, department_id=2)
        self.api.update_product(prod4)
        check_product('Mars', 90, False, False, 2)

        # test update price (negative prices are allowed!)
        prod5 = Product(id=1, price=-10)
        self.api.update_product(prod5)
        check_product('Mars', -10, False, False, 2)

        # test update without id
        prod6 = Product(name="Rafaelo")
        with self.assertRaises(FieldIsNone):
            self.api.update_product(prod6)
        # this should still be the same as before
        check_product('Mars', -10, False, False, 2)

        # test update with unknown id
        prod7 = Product(id=3, name="Rafaelo")
        with self.assertRaises(ObjectNotFound):
            self.api.update_product(prod7)
        # this should still be the same as before
        check_product('Mars', -10, False, False, 2)

        # test update with duplicate name
        prod8 = Product(id=1, name="Bounty")
        with self.assertRaises(DuplicateObject):
            self.api.update_product(prod8)
        # this should still be the same as before
        check_product('Mars', -10, False, False, 2)
