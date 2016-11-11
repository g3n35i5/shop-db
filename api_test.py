import sqlite3
import unittest
from models import Consumer, Product, Purchase, Deposit
from db_api import *
from validation import WrongType
import pdb


class TestDatabaseApi(unittest.TestCase):

    def setUpClass():
        # load the db schema
        with open('models.sql') as models:
            TestDatabaseApi.schema = models.read()

    def setUp(self):
        # create in memory db and create the tables
        self.con = sqlite3.connect(
            ':memory:', detect_types=sqlite3.PARSE_DECLTYPES)
        self.con.executescript(self.schema)

        self.api = DatabaseApi(self.con)

    def test_insert_consumer(self):
        # insert correctly
        c = Consumer(name='Hans Müller', active=True, credit=250)
        self.api.insert_object(c)
        consumer = self.api.get_one(table='consumer', id=1)
        self.assertEqual(consumer.name, 'Hans Müller')
        self.assertEqual(consumer.credit, 250)
        self.assertTrue(consumer.active)

        # missing fields
        with self.assertRaises(FieldIsNone):
            c = Consumer(name='Hans Müller', credit=250)
            self.api.insert_object(c)

        # insert wrong types
        with self.assertRaises(WrongType):
            c = Consumer(name=2, active=True, credit=250)

    def test_insert_product(self):
        # insert correctly
        p = Product(name='Twix', active=True, on_stock=True, price=90)
        self.api.insert_object(p)
        product = self.api.get_one(table='product', id=1)
        self.assertEqual(product.name, 'Twix')
        self.assertEqual(product.price, 90)
        self.assertTrue(product.active)
        self.assertTrue(product.on_stock)

        # missing fields
        with self.assertRaises(FieldIsNone):
            p = Product(name='Twix', price=250)
            self.api.insert_object(p)

        # insert wrong types
        with self.assertRaises(WrongType):
            p = Product(name=2, active=True, price=250)

    def test_update_consumer(self):
        c = Consumer(name='Hans Müller', active=True, credit=250)
        self.api.insert_object(c)
        consumer = self.api.get_one(table='consumer', id=1)
        self.assertEqual(consumer.name, 'Hans Müller')
        consumer.name = 'Peter Meier'
        self.api.update_consumer(consumer)
        consumer = self.api.get_one(table='consumer', id=1)
        self.assertEqual(consumer.name, 'Peter Meier')

    def test_access_wrong_table(self):
        with self.assertRaises(NonExistentTable):
            product = self.api.get_one(table='wrongtable', id=1)

    def test_get_product_by_name(self):
        p = Product(name='Mars', active=True, on_stock=False, price=30)
        self.api.insert_object(p)
        product = self.api.get_one(table='product', name='Mars')
        self.assertEqual(product.name, 'Mars')
        self.assertEqual(product.price, 30)
        self.assertTrue(product.active)
        self.assertFalse(product.on_stock)

    def test_get_product_by_id(self):
        p = Product(name='Twix', active=True, on_stock=True, price=90)
        self.api.insert_object(p)
        product = self.api.get_one(table='product', id=1)
        self.assertEqual(product.name, 'Twix')
        self.assertEqual(product.price, 90)
        self.assertTrue(product.active)
        self.assertTrue(product.on_stock)

    def test_get_products(self):
        p1 = Product(name='Mars', price=30, active=True, on_stock=False)
        p2 = Product(name='Twix', price=40, active=False, on_stock=True)
        self.api.insert_object(p1)
        self.api.insert_object(p2)

        products = self.api.get_all('product')
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
