#!/usr/bin/env python3

from flask import json
import sys
import pdb
import copy
from base import BaseTestCase

import project.backend.exceptions as exc


class WebapiTestCase(BaseTestCase):

    def assertException(self, res, exception):
        data = json.loads(res.data)
        exception = exc.exception_mapping[exception]
        self.assertEqual(res.status_code, exception['code'])
        self.assertEqual(data['code'], exception['code'])
        self.assertEqual(data['error_types'], exception['types'])

    def login(self, email, password):
        data = {'email': email, 'password': password}
        return self.client.post('/login',
                                data=json.dumps(data),
                                headers={'content-type': 'application/json'})

    def post(self, url, data, role):
        if role not in ['admin', 'extern', 'consumer']:
            sys.exit('Wrong role: {}'.format(role))

        if role == 'admin':
            id = 0
        elif role == 'extern':
            id = 3
        else:
            id = 1
        res = self.login(self.consumeremails[id], self.consumerpasswords[id])

        headers = {'content-type': 'application/json'}
        if role in ['admin', 'consumer']:
            headers['token'] = json.loads(res.data)['token']

        return self.client.post(url, data=json.dumps(data), headers=headers)

    def test_get_index(self):
        data = json.loads(self.client.get('/').data)
        self.assertEqual(data['types'], ['resource-not-found'])

    def test_list_consumers(self):
        consumers = json.loads(self.client.get('/consumers').data)
        self.assertEqual(len(consumers), 4)
        man = ['active', 'hasCredentials', 'id', 'isAdmin', 'name']
        forbidden = ['credit', 'email', 'password']
        for consumer in consumers:
            for m in man:
                assert m in consumer
            for f in forbidden:
                assert f not in consumer

        # Check admin access
        res = self.login(self.consumeremails[0], self.consumerpasswords[0])
        token = json.loads(res.data)['token']
        res = self.client.get('/consumers', headers={'token': token}).data
        consumers = json.loads(res)
        for consumer in consumers:
            assert 'email' in consumer
            assert 'credit' in consumer

    def test_insert_deposit(self):
        deposits = self.api.list_deposits()
        self.assertFalse(deposits)
        data = {'amount': 100, 'consumer_id': 1, 'comment': 'should not work'}
        res = self.post('/deposits', data, 'extern')
        self.assertEqual(res.status_code, 401)
        deposits = self.api.list_deposits()
        self.assertFalse(deposits)

        res = self.post('/deposits', data, 'consumer')
        self.assertEqual(res.status_code, 401)
        deposits = self.api.list_deposits()
        self.assertFalse(deposits)

        res = self.post('/deposits', data, 'admin')
        self.assertEqual(res.status_code, 201)
        deposits = self.api.list_deposits()
        self.assertEqual(len(deposits), 1)

    def test_insert_consumer(self):
        consumers = self.api.list_consumers()
        self.assertEqual(len(consumers), 4)

        # Test insert consumer with corrupt data
        # Test wrong type
        data = {'name': 2}
        res = self.post('/consumers', data, 'admin')
        self.assertException(res, exc.WrongType)

        # Test forbidden field
        data = {'name': 'Testperson', 'credit': 200}
        res = self.post('/consumers', data, 'admin')
        self.assertException(res, exc.ForbiddenField)

        # Test unknown field
        data = {'name': 'Testperson', 'coolness': 'over ninethousand'}
        res = self.post('/consumers', data, 'admin')
        self.assertException(res, exc.UnknownField)

        # Test duplicate object
        data = {'name': self.api.get_consumer(id=1).name}
        res = self.post('/consumers', data, 'admin')
        self.assertException(res, exc.DuplicateObject)

        # Test field is none
        data = {}
        res = self.post('/consumers', data, 'admin')
        self.assertException(res, exc.FieldIsNone)

        # Test minimum length undershot
        data = {'name': 'abc'}
        res = self.post('/consumers', data, 'admin')
        self.assertException(res, exc.MinLengthUndershot)

        # Test maximum length exceeded
        data = {'name': 'a'*65}
        res = self.post('/consumers', data, 'admin')
        self.assertEqual(res.status_code, 400)
        self.assertException(res, exc.MaxLengthExceeded)

        # Test insert consumer with correct data
        data = {'name': 'Testperson'}
        # Test insert without login data
        res = self.post('/consumers', data, 'extern')
        self.assertEqual(res.status_code, 401)

        # Test insert as consumer, which is not an administrator
        res = self.post('/consumers', data, 'consumer')
        self.assertEqual(res.status_code, 401)

        # Test insert as admin
        res = self.post('/consumers', data, 'admin')
        self.assertEqual(res.status_code, 201)

        # At this point only one new consumer should be added
        consumers = self.api.list_consumers()
        self.assertEqual(len(consumers), 5)
        self.assertEqual(consumers[4].name, data['name'])
        self.assertEqual(consumers[4].credit, 0)

    def test_insert_product(self):
        products = self.api.list_products()
        self.assertEqual(len(products), 3)

        b_data = {
            'name': 'Testproduct',
            'department_id': 1,
            'price': 200,
            'countable': True,
            'revocable': True
        }
        # Test insert product with corrupt data
        # Test wrong type
        data = b_data.copy()
        data['name'] = 2
        res = self.post('/products', data, 'admin')
        self.assertException(res, exc.WrongType)

        # Test forbidden field
        data = b_data.copy()
        data['active'] = True
        res = self.post('/products', data, 'admin')
        self.assertException(res, exc.ForbiddenField)

        # Test unknown field
        data = b_data.copy()
        data['bananas'] = 'foo'
        res = self.post('/products', data, 'admin')
        self.assertException(res, exc.UnknownField)

        # Test foreign key
        data = b_data.copy()
        data['department_id'] = 42
        res = self.post('/products', data, 'admin')
        self.assertException(res, exc.ForeignKeyNotExisting)

        # Test duplicate object
        data = b_data.copy()
        product = self.api.get_product(id=1)
        for key in product.__dict__['_data'].keys():
            if key in b_data:
                data[key] = getattr(product, key)

        res = self.post('/products', data, 'admin')
        self.assertException(res, exc.DuplicateObject)

        # Test field is none
        data = {}
        res = self.post('/products', data, 'admin')
        self.assertException(res, exc.FieldIsNone)

        # Test minimum length undershot
        data = b_data.copy()
        data['name'] = 'foo'
        res = self.post('/products', data, 'admin')
        self.assertException(res, exc.MinLengthUndershot)

        # Test maximum length exceeded
        data = b_data.copy()
        data['name'] = 'a'*65
        res = self.post('/products', data, 'admin')
        self.assertEqual(res.status_code, 400)
        self.assertException(res, exc.MaxLengthExceeded)

        data = {
                'name': 'Testproduct',
                'department_id': 1,
                'price': 200,
                'countable': True,
                'revocable': True
        }

        # Test insert without login data
        res = self.post('/products', data, 'extern')
        self.assertEqual(res.status_code, 401)

        # Test insert as consumer, which is not an administrator
        res = self.post('/products', data, 'consumer')
        self.assertEqual(res.status_code, 401)

        # Test insert as admin
        res = self.post('/products', data, 'admin')
        self.assertEqual(res.status_code, 201)

        # At this point only one new product should be added
        products = self.api.list_products()
        self.assertEqual(len(products), 4)

        for key in data.keys():
            self.assertEqual(getattr(products[3], key), data[key])

    def test_list_products(self):
        products = json.loads(self.client.get('/products').data)
        self.assertEqual(len(products), 3)

    def test_login(self):
        # Test wrong credentials
        res = self.login('me@test.com', 'this is not the correct password')
        self.assertEqual(res.status_code, 401)

        # Test correct credentials of an administrator
        res = self.login(self.consumeremails[0], self.consumerpasswords[0])
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)

        assert 'token' in data
        token = jwt.decode(data['token'], self.app.config['SECRET_KEY'])
        assert 'admin' in token
        assert 'consumer' not in token

        # Login consumer which is not an administrator
        res = self.login(self.consumeremails[1], self.consumerpasswords[1])
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)

        assert 'token' in data
        token = jwt.decode(data['token'], self.app.config['SECRET_KEY'])
        assert 'admin' not in token
        assert 'consumer' in token
