#!/usr/bin/env python3

from project.webapi import *
from flask_testing import TestCase
import project.configuration as config
import project.backend.models as models

passwords = None


def generate_passwords(pwds):
    global passwords
    if passwords is None:
        passwords = [None]*len(pwds)
        for i in range(0, len(pwds)):
            passwords[i] = bcrypt.generate_password_hash(pwds[i])
    return passwords


class BaseTestCase(TestCase):
    def create_app(self):
        return app

    def setUp(self):
        app, api = set_app(config.UnittestConfig)
        self.client = self.app.test_client()
        api.create_tables()
        self.api = api
        self.bcrypt = bcrypt

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
            {'name': 'Coffee', 'department_id': 1, 'price':  25},
            {'name': 'Twix',   'department_id': 2, 'price': 100},
            {'name': 'Pizza',  'department_id': 3, 'price': 400}
        ]
        for product in products:
            p = models.Product(name=product['name'], countable=True,
                               price=product['price'], revocable=True,
                               department_id=product['department_id'])
            self.api.insert_product(p)

        self.consumerpasswords = ['secret1', 'secret2', 'secret3', 'secret4']
        self.consumeremails = ['me1@test.com', 'me2@test.com',
                               'me3@test.com', 'me4@test.com', ]

        pwds = generate_passwords(self.consumerpasswords)
        c = models.Consumer(id=1)
        c.email = self.consumeremails[0]
        c.password = pwds[0]
        self.api.update_consumer(c)

        c = models.Consumer(id=2)
        c.email = self.consumeremails[1]
        c.password = pwds[1]
        self.api.update_consumer(c)

        consumer = self.api.get_consumer(id=1)
        department = self.api.get_department(id=1)
        self.api.setAdmin(consumer, department, True)

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
            {'name': 'Coffee', 'department_id': 1, 'price':  25},
            {'name': 'Twix',   'department_id': 2, 'price': 100},
            {'name': 'Pizza',  'department_id': 3, 'price': 400}
        ]
        api_products = self.api.list_products()
        assert len(api_products) == len(products)
        for i in range(0, len(api_products)):
            assert api_products[i].name == products[i]['name']

        # Check admin states
        lengths = [1, 0, 0, 0]
        for i in range(0, len(consumers)):
            roles = self.api.getAdminroles(consumers[i])
            self.assertEqual(len(roles), lengths[i])

    def tearDown(self):
        self.assertFalse(self.api.con.in_transaction)
