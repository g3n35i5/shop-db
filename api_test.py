import sqlite3
from models import Consumer, Product, Purchase, Deposit


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
