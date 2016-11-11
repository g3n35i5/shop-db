import sqlite3
import unittest
from models import Consumer, Product, Purchase, Deposit
from db_api import *
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

        # TODO: insert wrong types
