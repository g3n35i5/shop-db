#!/usr/bin/env python3

from flask import json
from base import BaseTestCase


class WebapiTestCase(BaseTestCase):

    def login(self, consumer_id, email, password):
        data = {'email': email, 'password': password}
        response = self.client.post('/login',
                                    data=json.dumps(data),
                                    headers={'content-type': 'application/json'})

        return {'data': response.data, 'code': response.status_code}

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

    def test_list_products(self):
        products = json.loads(self.client.get('/products').data)
        self.assertEqual(len(products), 3)

    def test_login(self):
        # Test wrong credentials
        res = self.login(1, 'me@test.com', 'this is not the correct password')
        self.assertEqual(res['code'], 401)

        # Test correct credentials of an administrator
        res = self.login(1, self.consumeremails[0], self.consumerpasswords[0])
        self.assertEqual(res['code'], 200)
        data = json.loads(res['data'])

        assert 'token' in data
        assert 'admin' in data
        assert 'consumer' not in data

        # Login consumer which is not an administrator
        res = self.login(2, self.consumeremails[1], self.consumerpasswords[1])
        self.assertEqual(res['code'], 200)
        data = json.loads(res['data'])

        assert 'token' in data
        assert 'admin' not in data
        assert 'consumer' in data
