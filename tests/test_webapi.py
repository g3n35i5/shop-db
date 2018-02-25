#!/usr/bin/env python3

from flask import json
import jwt
import sys
import pdb
import copy
import datetime
from base import BaseTestCase

import project.backend.exceptions as exc
import project.backend.models as models


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
        return self._request('post', url, data, role)

    def put(self, url, data, role):
        return self._request('put', url, data, role)

    def get(self, url, role):
        return self._request('get', url, {}, role)

    def _request(self, _type, url, data, role):
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

        if _type == 'post':
            res = self.client.post(url, data=json.dumps(data), headers=headers)
        elif _type == 'put':
            res = self.client.put(url, data=json.dumps(data), headers=headers)
        elif _type == 'get':
            res = self.client.get(url, data=json.dumps(data), headers=headers)
        else:
            sys.exit('Wrong request type: {}'.format(_type))

        return res

    def test_invalid_json(self):
        res = self.post('/products', None, 'admin')
        self.assertException(res, exc.InvalidJSON)

    def test_get_index(self):
        data = json.loads(self.client.get('/').data)
        self.assertEqual(data['types'], ['resource-not-found'])

    def test_get_status(self):
        data = json.loads(self.client.get('/status').data)
        self.assertTrue(data['result'])

    def test_token_expired(self):
        # TODO: Expire Token!
        pass

    def test_fake_admin(self):
        # Authentication as actual admin
        res = self.login(self.consumeremails[0], self.consumerpasswords[0])
        data = json.loads(res.data)
        baktoken_encoded = data['token']
        baktoken = jwt.decode(baktoken_encoded, self.app.config['SECRET_KEY'])

        # Manipulate id of admin
        token = baktoken.copy()
        token['admin']['id'] = 42

        headers = {
            'content-type': 'application/json',
            'token': token
        }
        data = {'amount': 100, 'consumer_id': 1, 'comment': 'should not work'}
        res = self.client.post('/deposits', data=json.dumps(data),
                               headers=headers)
        self.assertException(res, exc.TokenInvalid)

        # Try fake token
        headers = {
            'content-type': 'application/json',
            'token': 'i am not a valid token'.encode()
        }
        data = {'amount': 100, 'consumer_id': 1, 'comment': 'should not work'}
        res = self.client.post('/deposits', data=json.dumps(data),
                               headers=headers)
        self.assertException(res, exc.TokenInvalid)

        # Try corrupt token
        token = baktoken_encoded + 'strange tail'
        headers = {
            'content-type': 'application/json',
            'token': token
        }
        data = {'amount': 100, 'consumer_id': 1, 'comment': 'should not work'}
        res = self.client.post('/deposits', data=json.dumps(data),
                               headers=headers)
        self.assertException(res, exc.TokenInvalid)

    def test_get_consumer_purchases(self):
        # Get purchases of consumer 1. There shouldn't be any.
        res = self.get('/consumer/1/purchases', 'extern')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(len(data), 0)

        # Insert test purchases.
        purchase = models.Purchase(consumer_id=1, product_id=2,
                                   comment='Testpurchase 1', amount=1)
        self.api.insert_purchase(purchase)
        purchase = models.Purchase(consumer_id=1, product_id=1,
                                   comment='Testpurchase 2', amount=2)
        self.api.insert_purchase(purchase)

        # Get purchases of consumer 1. There should be 2 purchases.
        res = self.get('/consumer/1/purchases', 'extern')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['consumer_id'], 1)
        self.assertEqual(data[0]['product_id'], 2)
        self.assertEqual(data[0]['comment'], 'Testpurchase 1')
        self.assertEqual(data[0]['amount'], 1)

        self.assertEqual(data[1]['consumer_id'], 1)
        self.assertEqual(data[1]['product_id'], 1)
        self.assertEqual(data[1]['comment'], 'Testpurchase 2')
        self.assertEqual(data[1]['amount'], 2)

    def test_get_consumer_deposits(self):
        # Get deposits of consumer 1. There shouldn't be any.
        res = self.get('/consumer/1/deposits', 'extern')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(len(data), 0)

        # Insert test deposits.
        deposit = models.Deposit(consumer_id=1, comment='Testdeposit 1',
                                 amount=100)
        self.api.insert_deposit(deposit)
        deposit = models.Deposit(consumer_id=1, comment='Testdeposit 2',
                                 amount=200)
        self.api.insert_deposit(deposit)

        # Get deposits of consumer 1. There should be 2 deposits.
        res = self.get('/consumer/1/deposits', 'extern')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['consumer_id'], 1)
        self.assertEqual(data[0]['comment'], 'Testdeposit 1')
        self.assertEqual(data[0]['amount'], 100)

        self.assertEqual(data[1]['consumer_id'], 1)
        self.assertEqual(data[1]['comment'], 'Testdeposit 2')
        self.assertEqual(data[1]['amount'], 200)

    def test_get_product(self):
        res = self.get('/product/1', 'extern')
        self.assertEqual(res.status_code, 200)
        product = json.loads(res.data)
        self.assertEqual(product['name'], 'Coffee')
        self.assertEqual(product['department_id'], 1)
        self.assertEqual(product['price'], 25)

    def test_get_purchase(self):
        purchase = models.Purchase(consumer_id=1, product_id=2,
                                   comment='Testpurchase', amount=1)
        self.api.insert_purchase(purchase)
        res = self.get('/purchase/1', 'extern')
        self.assertEqual(res.status_code, 200)
        purchase = json.loads(res.data)
        self.assertEqual(purchase['consumer_id'], 1)
        self.assertEqual(purchase['product_id'], 2)
        self.assertEqual(purchase['amount'], 1)
        self.assertEqual(purchase['comment'], 'Testpurchase')
        self.assertFalse(purchase['revoked'])

    def test_list_purchases(self):
        # Insert test purchases
        consumer_ids = [1, 2, 3, 1, 1, 1, 3, 2, 3, 1]
        product_ids = [1, 1, 1, 2, 1, 3, 3, 2, 1, 3]
        amounts = [1, 8, 16, 5, 1, 5, 6, 7, 1, 2]
        for i in range(0, len(consumer_ids)):
            p = models.Purchase(consumer_id=consumer_ids[i],
                                product_id=product_ids[i],
                                amount=amounts[i],
                                comment='Purchase #{}'.format(i))
            self.api.insert_purchase(p)

        # List purchases without limit
        res = self.get('/purchases', 'extern')
        self.assertEqual(res.status_code, 200)
        pur = json.loads(res.data)
        self.assertEqual(len(pur), 10)
        for i in range(0, len(pur)):
            self.assertEqual(pur[i]['consumer_id'], consumer_ids[i])
            self.assertEqual(pur[i]['product_id'], product_ids[i])
            self.assertEqual(pur[i]['amount'], amounts[i])
            self.assertEqual(pur[i]['comment'], 'Purchase #{}'.format(i))

        # List purchases with limit
        res = self.get('/purchases/6', 'extern')
        self.assertEqual(res.status_code, 200)
        pur = json.loads(res.data)
        self.assertEqual(len(pur), 6)
        for i in range(0, len(pur)):
            self.assertEqual(pur[i]['consumer_id'], consumer_ids[9 - i])
            self.assertEqual(pur[i]['product_id'], product_ids[9 - i])
            self.assertEqual(pur[i]['amount'], amounts[9 - i])
            self.assertEqual(pur[i]['comment'], 'Purchase #{}'.format(9 - i))

    def test_list_departments(self):
        # List departments without token
        res = self.get('/departments', 'extern')
        departments = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(departments), 3)
        for department in departments:
            assert 'id' in department
            assert 'name' in department
            assert 'income_base' not in department
            assert 'income_karma' not in department
            assert 'expenses' not in department
            assert 'budget' not in department

        # List departments with token
        res = self.get('/departments', 'consumer')
        departments = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(departments), 3)
        for department in departments:
            assert 'id' in department
            assert 'name' in department
            assert 'income_base' in department
            assert 'income_karma' in department
            assert 'expenses' in department
            assert 'budget' in department

    def test_get_department_statistics(self):
        departments = self.api.list_departments()
        for department in departments:
            # Get without token, should fail
            res = self.get('/department/{}/statistics'.format(department.id),
                           'extern')
            self.assertException(res, exc.TokenMissing)

            # Get as consumer, should fail
            res = self.get('/department/{}/statistics'.format(department.id),
                           'consumer')
            self.assertException(res, exc.NotAuthorized)

            # Get as admin, should not fail
            res = self.get('/department/{}/statistics'.format(department.id),
                           'admin')
            self.assertEqual(res.status_code, 200)
            stats = json.loads(res.data)
            assert 'department_id' in stats
            assert 'purchase_times' in stats
            assert 'top_products' in stats

            self.assertEqual(stats['department_id'], department.id)
            self.assertEqual(type(stats['purchase_times']), dict)
            self.assertEqual(type(stats['top_products']), list)

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

    def test_consumer_favorite_products(self):
        res = self.get('/consumer/1/favorites', 'extern')
        self.assertEqual(res.status_code, 200)
        favorites = json.loads(res.data)
        self.assertEqual(type(favorites), list)
        self.assertEqual(len(favorites), 0)

        # Buy 3 product, 2 x product 1 and 1 x product 1
        purchase = models.Purchase(consumer_id=1, product_id=1, amount=1,
                                   comment='Testpurchase')
        self.api.insert_purchase(purchase)

        purchase = models.Purchase(consumer_id=1, product_id=1, amount=1,
                                   comment='Testpurchase')
        self.api.insert_purchase(purchase)

        purchase = models.Purchase(consumer_id=1, product_id=2, amount=1,
                                   comment='Testpurchase')
        self.api.insert_purchase(purchase)

        res = self.get('/consumer/1/favorites', 'extern')
        self.assertEqual(res.status_code, 200)
        favorites = json.loads(res.data)
        self.assertEqual(type(favorites), list)
        self.assertEqual(len(favorites), 2)
        self.assertEqual(favorites[0]['product_id'], 1)

    def test_insert_purchase(self):
        purchases = self.api.list_purchases()
        self.assertEqual(len(purchases), 0)
        b_data = {'consumer_id': 1, 'product_id': 1,
                  'amount': 1, 'comment': 'Default comment'}

        # Test insert purchase with corrupt data
        # Test wrong type
        data = b_data.copy()
        data['consumer_id'] = 'Hans'
        res = self.post('/purchases', data, 'extern')
        self.assertException(res, exc.WrongType)

        # Test maximum length exceeded
        data = b_data.copy()
        data['comment'] = 'A'*65
        res = self.post('/purchases', data, 'extern')
        self.assertException(res, exc.MaxLengthExceeded)

        # Test minimm length undershot
        data = b_data.copy()
        data['comment'] = 'Short'
        res = self.post('/purchases', data, 'extern')
        self.assertException(res, exc.MinLengthUndershot)

        # Test unknown field
        data = b_data.copy()
        data['name'] = 'Bananas'
        res = self.post('/purchases', data, 'extern')
        self.assertException(res, exc.UnknownField)

        # Test foreign key not existing
        data = b_data.copy()
        data['product_id'] = 5
        res = self.post('/purchases', data, 'extern')
        self.assertException(res, exc.ForeignKeyNotExisting)

        # Test field is none
        data = b_data.copy()
        del data['product_id']
        res = self.post('/purchases', data, 'extern')
        self.assertException(res, exc.FieldIsNone)

        # Test forbidden field
        data = b_data.copy()
        data['revoked'] = True
        res = self.post('/purchases', data, 'extern')
        self.assertException(res, exc.ForbiddenField)

        # Check consumers credit
        self.assertEqual(self.api.get_consumer(1).credit, 0)

        # Test insert purchase with correct data
        data = b_data.copy()
        res = self.post('/purchases', data, 'extern')
        self.assertEqual(res.status_code, 201)

        # At this point, only one purchase should have been inserted
        purchases = self.api.list_purchases()
        self.assertEqual(len(purchases), 1)
        self.assertEqual(purchases[0].consumer_id, data['consumer_id'])
        self.assertEqual(purchases[0].product_id, data['product_id'])
        self.assertEqual(purchases[0].amount, data['amount'])
        self.assertEqual(purchases[0].comment, data['comment'])
        self.assertFalse(purchases[0].revoked)

        # Check consumers credit
        self.assertEqual(self.api.get_consumer(1).credit, -25)

        # Revoke this purchase
        # Put request without data, nothing should happen
        res = self.put('/purchases/' + str(purchases[0].id), {}, 'extern')
        self.assertEqual(res.status_code, 200)
        self.assertFalse(self.api.get_purchase(1).revoked)

        # Check consumers credit
        self.assertEqual(self.api.get_consumer(1).credit, -25)

        # Put request with revoke command
        data = {'revoked': True}
        res = self.put('/purchases/' + str(purchases[0].id), data, 'extern')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(self.api.get_purchase(1).revoked)

        # Check consumers credit
        self.assertEqual(self.api.get_consumer(1).credit, 0)

        # Revoke purchase again, this should fail
        res = self.put('/purchases/' + str(purchases[0].id), data, 'extern')
        self.assertException(res, exc.CanOnlyBeRevokedOnce)

        # Check consumers credit
        self.assertEqual(self.api.get_consumer(1).credit, 0)

    def test_insert_deposit(self):
        deposits = self.api.list_deposits()
        self.assertFalse(deposits)
        data = {'amount': 100, 'consumer_id': 1, 'comment': 'should not work'}
        res = self.post('/deposits', data, 'extern')
        self.assertException(res, exc.TokenMissing)
        deposits = self.api.list_deposits()
        self.assertFalse(deposits)

        res = self.post('/deposits', data, 'consumer')
        self.assertException(res, exc.NotAuthorized)
        deposits = self.api.list_deposits()
        self.assertFalse(deposits)

        res = self.post('/deposits', data, 'admin')
        self.assertEqual(res.status_code, 201)
        deposits = self.api.list_deposits()
        self.assertEqual(len(deposits), 1)

    def test_insert_payoff(self):
        # TODO: Check payoffs
        pass

    def test_get_consumer(self):
        # Get consumer
        res = self.client.get('/consumer/1')
        self.assertEqual(res.status_code, 200)
        consumer = json.loads(res.data)
        apicon = self.api.get_consumer(1)
        self.assertEqual(consumer['name'], apicon.name)
        self.assertEqual(consumer['active'], apicon.active)
        self.assertEqual(consumer['credit'], apicon.credit)
        self.assertEqual(consumer['email'], apicon.email)
        self.assertEqual(consumer['hasCredentials'], apicon.hasCredentials)
        self.assertEqual(consumer['isAdmin'], apicon.isAdmin)
        self.assertEqual(consumer['karma'], apicon.karma)
        self.assertEqual(consumer['studentnumber'], apicon.studentnumber)

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
        self.assertException(res, exc.TokenMissing)

        # Test insert as consumer, which is not an administrator
        res = self.post('/consumers', data, 'consumer')
        self.assertException(res, exc.NotAuthorized)

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
        self.assertException(res, exc.TokenMissing)

        # Test insert as consumer, which is not an administrator
        res = self.post('/products', data, 'consumer')
        self.assertException(res, exc.NotAuthorized)

        # Test insert as admin
        res = self.post('/products', data, 'admin')
        self.assertEqual(res.status_code, 201)

        # At this point only one new product should be added
        products = self.api.list_products()
        self.assertEqual(len(products), 4)

        for key in data.keys():
            self.assertEqual(getattr(products[3], key), data[key])

    def test_update_consumer(self):
        # Create, insert and check Testperson
        consumer = models.Consumer(name='Testperson')
        self.api.insert_consumer(consumer)
        consumer = self.api.get_consumer(id=5)
        self.assertEqual(consumer.name, 'Testperson')
        self.assertEqual(consumer.email, None)
        self.assertEqual(consumer.credit, 0)
        self.assertTrue(consumer.active)
        self.assertEqual(consumer.karma, 0)
        self.assertEqual(consumer.studentnumber, None)
        adminroles = self.api.getAdminroles(consumer)
        self.assertEqual(len(adminroles), 0)

        # Test update name
        data = {'name': 'New Testperson'}
        res = self.put('/consumer/5', data, 'admin')
        self.assertEqual(res.status_code, 200)
        consumer = self.api.get_consumer(id=5)
        self.assertEqual(consumer.name, 'New Testperson')

        # Test update active state
        data = {'active': False}
        res = self.put('/consumer/5', data, 'admin')
        self.assertEqual(res.status_code, 200)
        consumer = self.api.get_consumer(id=5)
        self.assertFalse(consumer.active)

        # Test update multiple, simple
        data = {'active': True, 'name': 'Testperson', 'studentnumber': 42}
        res = self.put('/consumer/5', data, 'admin')
        self.assertEqual(res.status_code, 200)
        consumer = self.api.get_consumer(id=5)
        self.assertTrue(consumer.active)
        self.assertEqual(consumer.name, 'Testperson')
        self.assertEqual(consumer.studentnumber, 42)

        # Test set forbidden field
        data = {'credit': 100000}
        res = self.put('/consumer/5', data, 'admin')
        self.assertException(res, exc.ForbiddenField)

        # Test set adminroles while consumer does not have login data
        data = {'adminroles': {'1': True, '2': False}}
        res = self.put('/consumer/5', data, 'admin')
        self.assertException(res, exc.ConsumerNeedsCredentials)

        consumer = self.api.get_consumer(id=5)
        adminroles = self.api.getAdminroles(consumer)
        self.assertEqual(len(adminroles), 0)

        # Test set password, but no email
        data = {'password': 'Testpassword', 'repeatpassword': 'Testpassword'}
        res = self.put('/consumer/5', data, 'admin')
        self.assertException(res, exc.MissingData)

        # Test set password, but wrong repeatpassword
        data = {'password': 'Testpassword', 'repeatpassword': 'WrongRepeat'}
        res = self.put('/consumer/5', data, 'admin')
        self.assertException(res, exc.PasswordsDoNotMatch)

        # Test set email
        data = {'email': 'testconsumer@test.com'}
        res = self.put('/consumer/5', data, 'admin')

        # Check the new email adress
        consumer = self.api.get_consumer(id=5)
        self.assertEqual(consumer.email, 'testconsumer@test.com')

        # Get consumer via email should work now, too
        consumer = self.api.get_consumer_by_email('testconsumer@test.com')
        self.assertEqual(consumer.id, 5)
        self.assertEqual(consumer.name, 'Testperson')

        # Test set password without repeatpassword
        data = {'password': 'Testpassword'}
        res = self.put('/consumer/5', data, 'admin')
        self.assertException(res, exc.MissingData)

        # Test login. This should fail, because the consumer does not have
        # a password
        res = self.login('testconsumer@test.com', 'testpassword')
        self.assertException(res, exc.ConsumerNeedsCredentials)
        data = json.loads(res.data)
        assert 'token' not in data

        # Check whether the adminroles can be set.
        # This should still fail, because the consumer has stored an
        # email address, but no password.
        data = {'adminroles': {'1': True, '2': False}}
        res = self.put('/consumer/5', data, 'admin')
        self.assertException(res, exc.ConsumerNeedsCredentials)

        # Test set the consumer password
        data = {'password': 'Testpassword', 'repeatpassword': 'Testpassword'}
        res = self.put('/consumer/5', data, 'admin')
        self.assertEqual(res.status_code, 200)

        # Test check login.
        res = self.login('testconsumer@test.com', 'Testpassword')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'token' in data

        # Check whether the adminroles can be set.
        adminroles = self.api.getAdminroles(consumer)
        self.assertEqual(len(adminroles), 0)
        data = {'adminroles': {'1': False, '2': True, '3': True}}
        res = self.put('/consumer/5', data, 'admin')
        self.assertEqual(res.status_code, 200)
        adminroles = self.api.getAdminroles(consumer)
        self.assertEqual(len(adminroles), 2)
        self.assertEqual(adminroles[0].department_id, 2)
        self.assertEqual(adminroles[1].department_id, 3)

        # Test set adminrole again, nothing should happen
        data = {'adminroles': {'2': True}}
        res = self.put('/consumer/5', data, 'admin')
        self.assertEqual(res.status_code, 200)

        # Test change email adress
        data = {'email': 'updated@test.com'}
        res = self.put('/consumer/5', data, 'admin')
        self.assertEqual(res.status_code, 200)

        # Test login with the old email adress. This should fail.
        res = self.login('testconsumer@test.com', 'Testpassword')
        self.assertException(res, exc.ObjectNotFound)
        data = json.loads(res.data)
        assert 'token' not in data

        # Test check login with the new email adress
        res = self.login('updated@test.com', 'Testpassword')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'token' in data

        # Test remove adminroles
        data = {'adminroles': {'2': False, '3': False}}
        res = self.put('/consumer/5', data, 'admin')
        self.assertEqual(res.status_code, 200)
        adminroles = self.api.getAdminroles(consumer)
        self.assertEqual(len(adminroles), 0)

    def test_list_products(self):
        products = json.loads(self.client.get('/products').data)
        self.assertEqual(len(products), 3)

    def test_login(self):
        # Test wrong password
        res = self.login(self.consumeremails[0], 'wrong password')
        self.assertException(res, exc.NotAuthorized)

        # Test non existing mail
        res = self.login('me@test.com', 'this is not the correct password')
        self.assertException(res, exc.ObjectNotFound)

        # Test without mail adress
        res = self.client.post('/login',
                               data=json.dumps({'password': 'Test'}),
                               headers={'content-type': 'application/json'})
        self.assertException(res, exc.MissingData)

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
