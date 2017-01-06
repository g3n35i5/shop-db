import sqlite3
import unittest
import app
from .models import Consumer, Product, Purchase, Deposit
from .db_api import *
from .validation import WrongType
import pdb


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
        c = Consumer(name='Hans Müller', active=True, credit=250)
        self.api.insert_consumer(c)
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.name, 'Hans Müller')
        self.assertEqual(consumer.credit, 250)
        self.assertTrue(consumer.active)

        # missing fields
        with self.assertRaises(FieldIsNone):
            c = Consumer(name='Hans Müller', credit=250)
            self.api.insert_consumer(c)

        # insert wrong types
        with self.assertRaises(WrongType):
            c = Consumer(name=2, active=True, credit=250)

        c = Consumer(id=13, name='Hans', credit=12, active=True)
        with self.assertRaises(ForbiddenField):
            self.api.insert_consumer(c)

        # duplicate names should be rejected
        c = Consumer(name='Hans Müller', active=True, credit=0)
        with self.assertRaises(DuplicateObject):
            self.api.insert_consumer(c)

    def test_insert_product(self):
        # insert correctly
        p = Product(name='Twix', active=True, on_stock=True, price=90)
        self.api.insert_product(p)
        product = self.api.get_product(id=1)
        self.assertEqual(product.name, 'Twix')
        self.assertEqual(product.price, 90)
        self.assertTrue(product.active)
        self.assertTrue(product.on_stock)

        # missing fields
        with self.assertRaises(FieldIsNone):
            p = Product(name='Twix', price=250)
            self.api.insert_product(p)

        # insert wrong types
        with self.assertRaises(WrongType):
            p = Product(name=2, active=True, price=250)

        # product.id should be forbidden
        p = Product(id=1337, name="Mars", active=True, price=250,
                    on_stock=True)
        with self.assertRaises(ForbiddenField):
            self.api.insert_product(p)

        # duplicate names should be rejected
        c = Product(name='Twix', active=False, on_stock=False, price=30)
        with self.assertRaises(DuplicateObject):
            self.api.insert_product(c)

    def test_update_consumer(self):
        c = Consumer(name='Hans Müller', active=True, credit=250)
        self.api.insert_consumer(c)
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.name, 'Hans Müller')
        consumer.name = 'Peter Meier'
        self.api.update_consumer(consumer)
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.name, 'Peter Meier')

    def test_get_product_by_id(self):
        p = Product(name='Twix', active=True, on_stock=True, price=90)
        self.api.insert_product(p)
        product = self.api.get_product(id=1)
        self.assertEqual(product.name, 'Twix')
        self.assertEqual(product.price, 90)
        self.assertTrue(product.active)
        self.assertTrue(product.on_stock)

    def test_get_products(self):
        p1 = Product(name='Mars', price=30, active=True, on_stock=False)
        p2 = Product(name='Twix', price=40, active=False, on_stock=True)
        self.api.insert_product(p1)
        self.api.insert_product(p2)

        products = self.api.list_products()
        self.assertIs(type(products), list)
        self.assertEqual(len(products), 2)
        # Mars
        self.assertEqual(products[0].name, 'Mars')
        self.assertEqual(products[0].price, 30)
        self.assertTrue(products[0].active)
        self.assertFalse(products[0].on_stock)
        # Twix
        self.assertEqual(products[1].name, 'Twix')
        self.assertEqual(products[1].price, 40)
        self.assertFalse(products[1].active)
        self.assertTrue(products[1].on_stock)

    def test_create_deposit(self):
        # create test consumer
        c = Consumer(name='Hans Müller', active=True, credit=250)
        self.api.insert_consumer(c)

        # check the consumers credit
        consumer = self.api.get_consumer(1)
        self.assertEqual(consumer.credit, 250)

        # create deposit
        dep1 = Deposit(consumer_id=1, amount=250)
        self.api.insert_deposit(dep1)

        # check, if the consumers credit has been increased
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, 500)

        # check the results
        deposit = self.api.get_deposit(id=1)
        self.assertEqual(deposit.amount, 250)
        self.assertEqual(deposit.consumer_id, consumer.id)

        # test with wrong foreign_key consumer_id
        dep2 = Deposit(consumer_id=2, amount=240)
        with self.assertRaises(ForeignKeyNotExisting):
            self.api.insert_deposit(dep2)

        # deposit.id should be forbidden
        dep3 = Deposit(consumer_id=2, amount=20, id=12)
        with self.assertRaises(ForbiddenField):
            self.api.insert_deposit(dep3)

        # deposit.timestamp should be forbidden
        dep4 = Deposit(consumer_id=2, amount=20,
                       timestamp=datetime.datetime.now())
        with self.assertRaises(ForbiddenField):
            self.api.insert_deposit(dep3)

    def test_insert_purchase(self):
        # insert consumer and product
        p = Product(name='Coffee', price=20, active=True, on_stock=True)
        c = Consumer(name='Hans Müller', active=True, credit=250)
        self.api.insert_product(p)
        self.api.insert_consumer(c)

        # check, if the objects are correct
        consumer = self.api.get_consumer(id=1)
        product = self.api.get_product(id=1)
        self.assertEqual(consumer.credit, 250)
        self.assertEqual(product.price, 20)

        pur1 = Purchase(consumer_id=1, product_id=1, amount=5)
        self.api.insert_purchase(pur1)
        # TODO: pur.id is still None here. Should we change this?

        # test whether the purchase was inserted correctly
        pur2 = self.api.get_purchase(id=1)
        # paid_price should have been filled
        self.assertEqual(pur2.paid_price_per_product, 20)
        self.assertEqual(pur2.amount, 5)
        # timestamp should have been added
        self.assertIsNotNone(pur2.timestamp)

        consumer = self.api.get_consumer(1)
        self.assertEqual(consumer.credit,
                         250 - pur2.amount * pur2.paid_price_per_product)

        # test with wrong foreign key consumer_id
        pur3 = Purchase(consumer_id=2, product_id=1, amount=1)
        with self.assertRaises(ForeignKeyNotExisting):
            self.api.insert_purchase(pur3)

        # no new purchase should have been created
        self.assertEqual(len(self.api.list_purchases()), 1)

        # test with wrong foreign key product_id
        pur4 = Purchase(consumer_id=1, product_id=2, amount=1)
        with self.assertRaises(ForeignKeyNotExisting):
            self.api.insert_purchase(pur4)

        # no new purchase should have been created
        self.assertEqual(len(self.api.list_purchases()), 1)

        # the credit of the consumer must not have to be changed
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit,
                         250 - pur2.amount * pur2.paid_price_per_product)

        # purchase.id should be forbidden
        pur5 = Purchase(consumer_id=1, product_id=1, id=1337, amount=1)
        with self.assertRaises(ForbiddenField):
            self.api.insert_purchase(pur5)

        # purchase.paid_price should be forbidden
        pur6 = Purchase(consumer_id=1, product_id=1,
                        paid_price_per_product=200, amount=1)
        with self.assertRaises(ForbiddenField):
            self.api.insert_purchase(pur6)

        # purchase.revoked should be forbidden
        pur7 = Purchase(consumer_id=1, product_id=1, revoked=True, amount=1)
        with self.assertRaises(ForbiddenField):
            self.api.insert_purchase(pur7)

        # purchase.revoked should be forbidden
        pur8 = Purchase(consumer_id=1, product_id=1, amount=1,
                        timestamp=datetime.datetime.now())
        with self.assertRaises(ForbiddenField):
            self.api.insert_purchase(pur8)

    def test_update_purchase(self):
        # insert consumer and product
        p = Product(name='Coffee', price=20, active=True, on_stock=True)
        c = Consumer(name='Hans Müller', active=True, credit=250)
        self.api.insert_product(p)
        self.api.insert_consumer(c)

        # check, if the objects are correct
        consumer = self.api.get_consumer(id=1)
        product = self.api.get_product(id=1)
        self.assertEqual(consumer.credit, 250)
        self.assertEqual(product.price, 20)

        pur = Purchase(consumer_id=1, product_id=1, amount=5)
        self.api.insert_purchase(pur)

        # check if the consumers credit has decreased
        pur = self.api.get_purchase(id=1)
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit,
                         250 - pur.amount * pur.paid_price_per_product)

        # revoke purchase
        pur.revoked = True
        self.api.update_purchase(pur)

        # check if the purchase has been updated
        pur2 = self.api.get_purchase(id=1)
        self.assertTrue(pur2.revoked)

        # check if the consumers credit has increased
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, 250)

    def test_update_product(self):
        # create test products
        prod1 = Product(name='Twix', active=True, on_stock=True, price=90)
        self.api.insert_product(prod1)
        prod2 = Product(name='Bounty', active=True, on_stock=False, price=80)
        self.api.insert_product(prod2)

        # define a shortcut to test the state of the product with id=1
        def check_product(name, price, active, on_stock):
            # check whether the product was inserted correctly
            prod = self.api.get_product(id=1)
            self.assertEqual(prod.name, name)
            self.assertEqual(prod.price, price)
            self.assertEqual(prod.active, active)
            self.assertEqual(prod.on_stock, on_stock)

        # test update name
        prod3 = Product(id=1, name='Mars')
        self.api.update_product(prod3)
        check_product('Mars', 90, True, True)

        # test update active and on_stock
        prod4 = Product(id=1, active=False, on_stock=False)
        self.api.update_product(prod4)
        check_product('Mars', 90, False, False)

        # test update price (negative prices are allowed!)
        prod5 = Product(id=1, price=-10)
        self.api.update_product(prod5)
        check_product('Mars', -10, False, False)

        # test update without id
        prod6 = Product(name="Rafaelo")
        with self.assertRaises(FieldIsNone):
            self.api.update_product(prod6)
        # this should still be the same as before
        check_product('Mars', -10, False, False)

        # test update with unknown id
        prod7 = Product(id=3, name="Rafaelo")
        with self.assertRaises(ObjectNotFound):
            self.api.update_product(prod7)
        # this should still be the same as before
        check_product('Mars', -10, False, False)

        # test update with duplicate name
        prod8 = Product(id=1, name="Bounty")
        with self.assertRaises(DuplicateObject):
            self.api.update_product(prod8)
        # this should still be the same as before
        check_product('Mars', -10, False, False)
