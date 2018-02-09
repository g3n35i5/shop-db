#!/usr/bin/env python3

from project.webapi import *
from flask_testing import TestCase
import project.configuration as config
import project.backend.models as models


class BaseTestCase(TestCase):
    def create_app(self):
        return app

    def setUp(self):
        app, api = set_app(config.UnittestConfig)
        self.client = self.app.test_client()
        api.create_tables()
        self.api = api

        # Create default consumers
        names = ['William Jones', 'Mary Smith', 'Bryce Jones', 'Daniel Lee']
        for name in names:
            consumer = models.Consumer(name=name)
            self.api.insert_consumer(consumer)

        # Create default departments
        names = ['Drinks', 'Sweets', 'Food']
        for name in names:
            department = models.Department(name=name, budget=20000)
            self.api.insert_department(department)

        # Create default products
        products = [
            {'name': 'Coffee', 'department_id': 1, 'price': 25 },
            {'name': 'Twix',   'department_id': 2, 'price': 100},
            {'name': 'Pizza',  'department_id': 3, 'price': 400}
        ]
        for product in products:
            p = models.Product(name=product['name'], countable=True,
                               price=product['price'], revocable=True,
                               department_id=product['department_id'])
            self.api.insert_product(p)

    def test_default_elements(self):
        # Check if all consumers have been entered correctly
        names = ['William Jones', 'Mary Smith', 'Bryce Jones', 'Daniel Lee']
        consumers = self.api.list_consumers()
        assert len(consumers) == len(names)
        for i in range(0, len(consumers)):
            assert consumers[i].name == names[i]

        # Check if all departments have been entered correctly
        names = ['Drinks', 'Sweets', 'Food']
        departments = self.api.list_departments()
        assert len(departments) == len(names)
        for i in range(0, len(departments)):
            assert departments[i].name == names[i]

        # Check if all products have been entered correctly
        products = [
            {'name': 'Coffee', 'department_id': 1, 'price': 25 },
            {'name': 'Twix',   'department_id': 2, 'price': 100},
            {'name': 'Pizza',  'department_id': 3, 'price': 400}
        ]
        api_products = self.api.list_products()
        assert len(api_products) == len(products)
        for i in range(0, len(api_products)):
            assert api_products[i].name == products[i]['name']


    def tearDown(self):
        self.assertFalse(self.api.con.in_transaction)
