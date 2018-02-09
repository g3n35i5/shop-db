#!/usr/bin/env python3

from flask import json
import sys
import pdb
from base import BaseTestCase


class WebapiTestCase(BaseTestCase):

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
            headers[role] = json.loads(res.data)[role]

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
        assert 'admin' in data
        assert 'consumer' not in data

        # Login consumer which is not an administrator
        res = self.login(self.consumeremails[1], self.consumerpasswords[1])
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)

        assert 'token' in data
        assert 'admin' not in data
        assert 'consumer' in data
