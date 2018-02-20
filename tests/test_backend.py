#!/usr/bin/env python3

import time
from base import BaseTestCase
from project.backend.db_api import *
from project.backend.validation import *
import project.backend.models as models


class BackendTestCase(BaseTestCase):
    def test_get_top_products(self):
        # buy 3x Coffee and 2x Twix
        for i in range(0, 3):
            pur = models.Purchase(consumer_id=1, product_id=1, amount=1,
                                  comment="bought with karma")
            self.api.insert_purchase(pur)
        for i in range(0, 2):
            pur = models.Purchase(consumer_id=1, product_id=2, amount=1,
                                  comment="bought with karma")
            self.api.insert_purchase(pur)

        top = self.api.get_top_products(department_id=2, num_products=2)
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0][0], 1)
        self.assertEqual(top[0][1], 3)
        self.assertEqual(top[1][0], 2)
        self.assertEqual(top[1][1], 2)

    def test_insert_consumer(self):
        # insert correctly
        c = models.Consumer(name='Hans Müller', email='me@example.com')
        self.api.insert_consumer(c)
        consumer = self.api.get_consumer(id=5)
        self.assertEqual(consumer.name, 'Hans Müller')
        self.assertEqual(consumer.email, 'me@example.com')
        self.assertEqual(consumer.credit, 0)
        self.assertEqual(consumer.karma, 0)
        self.assertTrue(consumer.active)

        # insert second consumer
        c = models.Consumer(name='Peter Meier', email='me@example.com')
        with self.assertRaises(exc.DuplicateObject):
            self.api.insert_consumer(c)

        # missing fields
        with self.assertRaises(exc.FieldIsNone):
            c = models.Consumer()
            self.api.insert_consumer(c)

        # insert wrong types
        with self.assertRaises(exc.WrongType):
            c = models.Consumer(name=2)

        # id should be forbidden
        c = models.Consumer(id=13, name='Hans')
        with self.assertRaises(exc.ForbiddenField):
            self.api.insert_consumer(c)

        # credit should be forbidden
        c = models.Consumer(name='Hans', credit=12)
        with self.assertRaises(exc.ForbiddenField):
            self.api.insert_consumer(c)

        # duplicate names should be rejected
        c = models.Consumer(name='Hans Müller')
        with self.assertRaises(exc.DuplicateObject):
            self.api.insert_consumer(c)

    def test_update_consumer(self):
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.name, 'William Jones')
        self.assertEqual(consumer.karma, 0)
        consumer = models.Consumer(id=1)
        self.api.update_consumer(consumer)
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.name, 'William Jones')
        consumer = models.Consumer(id=1, karma=10)
        self.api.update_consumer(consumer)
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.karma, 10)

        # test karmahistory
        consumer = models.Consumer(id=1, karma=9)
        self.api.update_consumer(consumer)

        consumer = models.Consumer(id=1, karma=8)
        self.api.update_consumer(consumer)

        consumer = models.Consumer(id=1, karma=7)
        self.api.update_consumer(consumer)

        c = models.Consumer(id=1, credit=1337)
        with self.assertRaises(exc.ForbiddenField):
            self.api.update_consumer(c)
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, 0)

        c = models.Consumer(active=False)
        with self.assertRaises(exc.FieldIsNone):
            self.api.update_consumer(c)

    def test_departmentpurchase(self):
        # Make consumer 1 administrator
        upconsumer = models.Consumer(id=1)
        upconsumer.email = 'me@example.com'
        upconsumer.password = 'supersecretpassword'.encode()
        self.api.update_consumer(upconsumer)

        consumer = self.api.get_consumer(id=1)
        departments = self.api.list_departments()
        self.api.setAdmin(consumer, departments[0], True)

        self.assertEqual(departments[0].expenses, 0)
        self.assertEqual(departments[1].expenses, 0)
        self.assertEqual(departments[2].expenses, 0)

        product = self.api.get_product(id=1)
        self.assertEqual(product.stock, 0)

        dpurchase = models.Departmentpurchase()
        dpurchase.product_id = product.id
        dpurchase.department_id = departments[0].id
        dpurchase.admin_id = consumer.id
        dpurchase.amount = 5
        dpurchase.price_per_product = 10
        dpurchase.admin_id = 1

        self.api.insert_departmentpurchase(dpurchase)
        dpurchases = self.api.list_departmentpurchases(department_id=1)
        self.assertEqual(len(dpurchases), 1)

        product = self.api.get_product(id=1)
        self.assertEqual(product.stock, dpurchase.amount)

        payoffs = self.api.list_payoffs()
        self.assertEqual(len(payoffs), 1)
        comment = '{}x {}'.format(dpurchase.amount, product.name)
        self.assertEqual(payoffs[0].comment, comment)

        departments = self.api.list_departments()
        self.assertEqual(departments[0].expenses, 50)
        self.assertEqual(departments[1].expenses, 0)
        self.assertEqual(departments[2].expenses, 0)

        # Revoke deposit in order to "revoke" departmentpurchase
        p = models.Payoff(id=1, revoked=True, admin_id=1)
        self.api.update_payoff(p)

        departments = self.api.list_departments()
        self.assertEqual(departments[0].expenses, 0)
        self.assertEqual(departments[1].expenses, 0)
        self.assertEqual(departments[2].expenses, 0)

        product = self.api.get_product(id=1)
        self.assertEqual(product.stock, 0)

        department = self.api.get_department(id=1)
        self.assertEqual(department.expenses, 0)

        with self.assertRaises(exc.CanOnlyBeRevokedOnce):
            p = models.Payoff(id=1, revoked=True)
            self.api.update_payoff(p)

        departments = self.api.list_departments()
        self.assertEqual(departments[0].expenses, 0)
        self.assertEqual(departments[1].expenses, 0)
        self.assertEqual(departments[2].expenses, 0)

    def test_insert_consumers(self):
        d = models.Department(name="Test 1", budget=20000)
        self.api.insert_department(d)
        d = models.Department(name="Test 2", budget=30000)
        self.api.insert_department(d)
        d = models.Department(name="Test 3", budget=40000)
        self.api.insert_department(d)

        departments = self.api.list_departments()
        self.assertEqual(len(departments), 6)

        # check id's
        self.assertEqual(departments[3].id, 4)
        self.assertEqual(departments[4].id, 5)
        self.assertEqual(departments[5].id, 6)

        # check names
        self.assertEqual(departments[3].name, "Test 1")
        self.assertEqual(departments[4].name, "Test 2")
        self.assertEqual(departments[5].name, "Test 3")

        # check incomes
        self.assertEqual(departments[3].income_base, 0)
        self.assertEqual(departments[4].income_base, 0)
        self.assertEqual(departments[5].income_base, 0)

        self.assertEqual(departments[3].income_karma, 0)
        self.assertEqual(departments[4].income_karma, 0)
        self.assertEqual(departments[5].income_karma, 0)

        # check expenses
        self.assertEqual(departments[3].expenses, 0)
        self.assertEqual(departments[4].expenses, 0)
        self.assertEqual(departments[5].expenses, 0)

        # check expenses
        self.assertEqual(departments[3].budget, 20000)
        self.assertEqual(departments[4].budget, 30000)
        self.assertEqual(departments[5].budget, 40000)

    def test_insert_products(self):
        p = models.Product(name='Test 1', countable=True, price=100,
                           department_id=1, revocable=True)
        self.api.insert_product(p)
        product = self.api.get_product(id=4)
        self.assertEqual(product.name, 'Test 1')
        self.assertEqual(product.price, 100)
        self.assertEqual(product.department_id, 1)
        self.assertTrue(product.active)
        self.assertEqual(product.stock, 0)

        # missing fields
        with self.assertRaises(exc.FieldIsNone):
            p = models.Product(name='Test 1', price=250)
            self.api.insert_product(p)

        # insert wrong types
        with self.assertRaises(exc.WrongType):
            p = models.Product(name=2, countable=True,
                               price=100, department_id=1, revocable=True)

        # product.id should be forbidden
        p = models.Product(id=10, name='Test 1', countable=True,
                           price=100, department_id=1, revocable=True)
        with self.assertRaises(exc.ForbiddenField):
            self.api.insert_product(p)

        # duplicate names should be rejected
        p = models.Product(name='Test 1', countable=True,
                           price=100, department_id=1, revocable=True)
        with self.assertRaises(exc.DuplicateObject):
            self.api.insert_product(p)

    def test_adminroles(self):
        consumer = self.api.get_consumer(id=3)
        department = self.api.get_department(id=1)

        # Make sure, that the consumer is no admin
        adminroles = self.api.getAdminroles(consumer)
        self.assertEqual(len(adminroles), 0)

        # Make sure, that the consumer needs email and password to be admin
        with self.assertRaises(exc.ConsumerNeedsCredentials):
                self.api.setAdmin(consumer, department, True)

        # Update the consumer, so he can be admin
        upconsumer = models.Consumer(id=consumer.id)
        upconsumer.email = 'me@example.com'
        upconsumer.password = 'supersecretpassword'.encode()

        self.api.update_consumer(upconsumer)
        consumer = self.api.get_consumer(id=3)

        # Make consumer admin for department 1
        self.api.setAdmin(consumer, department, True)
        adminroles = self.api.getAdminroles(consumer)
        self.assertEqual(adminroles[0].department_id, 1)
        self.assertEqual(len(adminroles), 1)

        # Make consumer admin for the same department. Nothing should happen
        self.api.setAdmin(consumer, department, True)
        adminroles = self.api.getAdminroles(consumer)
        self.assertEqual(adminroles[0].department_id, 1)
        self.assertEqual(len(adminroles), 1)

        # Delete consumer admin role for department 1
        self.api.setAdmin(consumer, department, False)
        adminroles = self.api.getAdminroles(consumer)
        self.assertEqual(len(adminroles), 0)

    def test_get_product_by_id(self):
        product = self.api.get_product(id=1)
        self.assertEqual(product.name, 'Coffee')
        self.assertEqual(product.price, 25)
        self.assertEqual(product.department_id, 1)
        self.assertTrue(product.active)
        self.assertEqual(product.stock, 0)

    def test_list_products(self):
        products = self.api.list_products()
        self.assertIs(type(products), list)
        self.assertEqual(len(products), 3)

        # Coffee
        self.assertEqual(products[0].name, 'Coffee')
        self.assertEqual(products[0].price, 25)
        self.assertEqual(products[0].department_id, 1)
        self.assertTrue(products[0].active)
        self.assertEqual(products[0].stock, 0)
        # Twix
        self.assertEqual(products[1].name, 'Twix')
        self.assertEqual(products[1].price, 100)
        self.assertEqual(products[1].department_id, 2)
        self.assertTrue(products[1].active)
        self.assertEqual(products[1].stock, 0)
        # Pizza
        self.assertEqual(products[2].name, 'Pizza')
        self.assertEqual(products[2].price, 400)
        self.assertEqual(products[2].department_id, 3)
        self.assertTrue(products[2].active)
        self.assertEqual(products[2].stock, 0)

    def test_create_payoff(self):

        # Check bank balance
        bank = self.api.get_bank()
        self.assertEqual(bank.credit, 0)

        # Check department expenses
        departments = self.api.list_departments()
        self.assertEqual(departments[0].expenses, 0)
        self.assertEqual(departments[1].expenses, 0)
        self.assertEqual(departments[2].expenses, 0)

        # Check payoffs
        payoffs = self.api.list_payoffs()
        self.assertEqual(len(payoffs), 0)

        # Make consumer 2 administrator for department 2
        upconsumer = models.Consumer(id=2)
        upconsumer.email = 'me@example.com'
        upconsumer.password = 'supersecretpassword'.encode()
        self.api.update_consumer(upconsumer)
        consumer = self.api.get_consumer(upconsumer.id)
        self.api.setAdmin(consumer, departments[1], True)

        # Check consumer admin states
        consumers = self.api.list_consumers()
        self.assertEqual(len(consumers), 4)
        self.assertTrue(consumers[0].isAdmin)
        self.assertTrue(consumers[1].isAdmin)
        self.assertFalse(consumers[2].isAdmin)
        self.assertFalse(consumers[3].isAdmin)

        # Check adminroles of consumer 1
        adminroles = self.api.getAdminroles(consumers[0])
        self.assertEqual(len(adminroles), 1)
        self.assertEqual(adminroles[0].consumer_id, consumers[0].id)
        self.assertEqual(adminroles[0].department_id, departments[0].id)

        # Check adminroles of consumer 2
        adminroles = self.api.getAdminroles(consumers[1])
        self.assertEqual(len(adminroles), 1)
        self.assertEqual(adminroles[0].consumer_id, consumers[1].id)
        self.assertEqual(adminroles[0].department_id, departments[1].id)

        # Consumer No. 1 is administrator for department 1 and should
        # therefore be able to insert a payoff
        payoff_1 = models.Payoff(department_id=1, comment='Should work',
                                 amount=10000, admin_id=1)
        self.api.insert_payoff(payoff_1)

        # Now it is necessary to check whether even a payoff and an admin
        # event have been created and whether all values are set correctly.
        payoffs = self.api.list_payoffs()
        self.assertEqual(len(payoffs), 1)
        self.assertEqual(payoffs[0].department_id, payoff_1.department_id)
        self.assertEqual(payoffs[0].comment, payoff_1.comment)
        self.assertEqual(payoffs[0].amount, payoff_1.amount)

        # Check bank balance
        bank = self.api.get_bank()
        self.assertEqual(bank.credit, -10000)

        # Check that the expenses of the departments are correct
        departments = self.api.list_departments()
        self.assertEqual(departments[0].expenses, 10000)
        self.assertEqual(departments[1].expenses, 0)
        self.assertEqual(departments[2].expenses, 0)

        # Try to set revoke to false, this should fail
        p = models.Payoff(id=1, revoked=False, admin_id=1)
        with self.assertRaises(exc.NothingHasChanged):
            self.api.update_payoff(p)

        # revoke payoff
        p = models.Payoff(id=1, revoked=True, admin_id=1)
        self.api.update_payoff(p)

        bank = self.api.get_bank()
        self.assertEqual(bank.credit, 0)
        departments = self.api.list_departments()
        self.assertEqual(departments[0].expenses, 0)
        self.assertEqual(departments[1].expenses, 0)
        self.assertEqual(departments[2].expenses, 0)

        with self.assertRaises(exc.CanOnlyBeRevokedOnce):
            self.api.update_payoff(p)

        departments = self.api.list_departments()
        self.assertEqual(departments[0].expenses, 0)
        self.assertEqual(departments[1].expenses, 0)
        self.assertEqual(departments[2].expenses, 0)

        # Try to un-revoke payoff, this should fail
        p = models.Payoff(id=1, revoked=False, admin_id=1)
        with self.assertRaises(exc.RevokeIsFinal):
            self.api.update_payoff(p)

        departments = self.api.list_departments()
        self.assertEqual(departments[0].expenses, 0)
        self.assertEqual(departments[1].expenses, 0)
        self.assertEqual(departments[2].expenses, 0)

    def test_create_deposit(self):
        # check the consumers credit
        consumer = self.api.get_consumer(1)
        self.assertEqual(consumer.credit, 0)

        # create deposit
        dep1 = models.Deposit(consumer_id=1, amount=250, comment="testcomment")
        self.api.insert_deposit(dep1)

        # check, if the consumers credit has been increased
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, 250)

        # check the results
        deposit = self.api.get_deposit(id=1)
        self.assertEqual(deposit.amount, 250)
        self.assertEqual(deposit.comment, "testcomment")
        self.assertEqual(deposit.consumer_id, consumer.id)

        # test with wrong foreign_key consumer_id
        dep2 = models.Deposit(consumer_id=5, amount=240, comment="testcomment")
        with self.assertRaises(exc.ForeignKeyNotExisting):
            self.api.insert_deposit(dep2)

        # deposit.id should be forbidden
        dep3 = models.Deposit(consumer_id=2, amount=20,
                              id=12, comment="testcomment")
        with self.assertRaises(exc.ForbiddenField):
            self.api.insert_deposit(dep3)

        # deposit.timestamp should be forbidden
        dep4 = models.Deposit(consumer_id=2, amount=20, comment="testcomment",
                              timestamp=datetime.datetime.now())
        with self.assertRaises(exc.ForbiddenField):
            self.api.insert_deposit(dep3)

    def test_insert_purchase(self):
        department = self.api.get_department(id=1)
        self.assertEqual(department.id, 1)
        self.assertEqual(department.name, "Drinks")
        self.assertEqual(department.income_base, 0)
        self.assertEqual(department.income_karma, 0)
        self.assertEqual(department.expenses, 0)
        self.assertEqual(department.budget, 20000)

        # insert consumer and product
        c2 = models.Consumer(id=2, karma=10)
        c3 = models.Consumer(id=3, karma=-10)

        self.api.update_consumer(c2)
        self.api.update_consumer(c3)

        # check consumers
        consumers = self.api.list_consumers()
        self.assertEqual(len(consumers), 4)
        self.assertEqual(consumers[0].credit, 0)
        self.assertEqual(consumers[1].credit, 0)
        self.assertEqual(consumers[2].credit, 0)
        self.assertEqual(consumers[3].credit, 0)

        self.assertEqual(consumers[0].karma, 0)
        self.assertEqual(consumers[1].karma, 10)
        self.assertEqual(consumers[2].karma, -10)
        self.assertEqual(consumers[3].karma, 0)

        # check, if the objects are correct
        product = self.api.get_product(id=1)
        self.assertEqual(product.price, 25)

        # Turn on use karma
        self.api.configuration['USE_KARMA'] = True

        pur1 = models.Purchase(consumer_id=1, product_id=1, amount=1,
                               comment="good dude buys something")

        pur2 = models.Purchase(consumer_id=2, product_id=1, amount=1,
                               comment="awesome dude buys something")

        pur3 = models.Purchase(consumer_id=3, product_id=1, amount=1,
                               comment="bad dude buys something")

        self.api.insert_purchase(pur1)
        self.api.insert_purchase(pur2)
        self.api.insert_purchase(pur3)

        # get purchases
        purchases = self.api.list_purchases()
        self.assertEqual(len(purchases), 3)

        self.assertEqual(purchases[0].paid_base_price_per_product, 25)
        self.assertEqual(purchases[0].paid_karma_per_product, 5)
        self.assertEqual(purchases[0].amount, 1)
        self.assertEqual(purchases[0].comment, "good dude buys something")
        self.assertIsNotNone(purchases[0].timestamp)

        self.assertEqual(purchases[1].paid_base_price_per_product, 25)
        self.assertEqual(purchases[1].paid_karma_per_product, 0)
        self.assertEqual(purchases[1].amount, 1)
        self.assertEqual(purchases[1].comment, "awesome dude buys something")
        self.assertIsNotNone(purchases[1].timestamp)

        self.assertEqual(purchases[2].paid_base_price_per_product, 25)
        self.assertEqual(purchases[2].paid_karma_per_product, 10)
        self.assertEqual(purchases[2].amount, 1)
        self.assertEqual(purchases[2].comment, "bad dude buys something")
        self.assertIsNotNone(purchases[2].timestamp)

        # check consumers
        consumers = self.api.list_consumers()
        self.assertEqual(len(consumers), 4)
        self.assertEqual(consumers[0].credit, -30)
        self.assertEqual(consumers[1].credit, -25)
        self.assertEqual(consumers[2].credit, -35)
        self.assertEqual(consumers[3].credit, 0)

        department = self.api.get_department(id=1)
        self.assertEqual(department.id, 1)
        self.assertEqual(department.name, "Drinks")
        self.assertEqual(department.income_base, 75)
        self.assertEqual(department.income_karma, 15)
        self.assertEqual(department.expenses, 0)
        self.assertEqual(department.budget, 20000)

        # now we revoke the purchases
        pur = models.Purchase(id=1, revoked=True)
        self.api.update_purchase(pur)
        department = self.api.get_department(id=1)
        self.assertEqual(department.income_base, 50)
        self.assertEqual(department.income_karma, 10)

        pur = models.Purchase(id=2, revoked=True)
        self.api.update_purchase(pur)
        department = self.api.get_department(id=1)
        self.assertEqual(department.income_base, 25)
        self.assertEqual(department.income_karma, 10)

        pur = models.Purchase(id=3, revoked=True)
        self.api.update_purchase(pur)
        department = self.api.get_department(id=1)
        self.assertEqual(department.income_base, 0)
        self.assertEqual(department.income_karma, 0)

        # test with wrong foreign key consumer_id
        pur4 = models.Purchase(consumer_id=5, product_id=1, amount=1,
                               comment="purchase done by unittest")
        with self.assertRaises(exc.ForeignKeyNotExisting):
            self.api.insert_purchase(pur4)

        # no new purchase should have been created
        self.assertEqual(len(self.api.list_purchases()), 3)

        # test with wrong foreign key product_id
        pur5 = models.Purchase(consumer_id=1, product_id=4, amount=1,
                               comment="purchase done by unittest")
        with self.assertRaises(exc.ForeignKeyNotExisting):
            self.api.insert_purchase(pur5)

        # no new purchase should have been created
        self.assertEqual(len(self.api.list_purchases()), 3)

        # the credit of the consumer must not have to be changed
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, 0)

        # purchase.id should be forbidden
        pur6 = models.Purchase(consumer_id=1, product_id=1, id=1337, amount=1,
                               comment="purchase done by unittest")
        with self.assertRaises(exc.ForbiddenField):
            self.api.insert_purchase(pur6)

        # purchase.paid_base_price_per_product and paid_karma_per_product
        # should be forbidden
        pur7 = models.Purchase(consumer_id=1, product_id=1,
                               paid_base_price_per_product=200,
                               paid_karma_per_product=200,
                               amount=1,
                               comment="purchase done by unittest")
        with self.assertRaises(exc.ForbiddenField):
            self.api.insert_purchase(pur7)

        # purchase.revoked should be forbidden
        pur8 = models.Purchase(consumer_id=1, product_id=1, revoked=True,
                               amount=1, comment="purchase done by unittest")
        with self.assertRaises(exc.ForbiddenField):
            self.api.insert_purchase(pur8)

        # purchase.revoked should be forbidden
        pur9 = models.Purchase(consumer_id=1, product_id=1, amount=1,
                               timestamp=datetime.datetime.now(),
                               comment="purchase done by unittest")
        with self.assertRaises(exc.ForbiddenField):
            self.api.insert_purchase(pur9)

    def test_inventory_system(self):
        p = models.Product(id=1, stock=10)
        self.api.update_product(p)

        p = self.api.get_product(id=1)
        self.assertEqual(p.stock, 10)
        self.assertTrue(p.countable)

        for i in range(1, 6):
            pur = models.Purchase(consumer_id=1, product_id=1,
                                  amount=2, comment='testing inventory')
            self.api.insert_purchase(pur)

        p = self.api.get_product(id=1)
        self.assertEqual(p.stock, 0)

        for i in range(1, 3):
            pur = models.Purchase(id=i,
                                  revoked=True,
                                  comment='revoking purchase')
            self.api.update_purchase(pur)

        p = self.api.get_product(id=1)
        self.assertEqual(p.stock, 4)

        # check non countable products
        p = models.Product(name='Water', countable=False,
                           price=20, department_id=2, revocable=True)

        self.api.insert_product(p)
        p = self.api.get_product(id=4)
        self.assertFalse(p.countable)
        self.assertEqual(p.stock, None)

        pur = models.Purchase(consumer_id=1, product_id=4,
                              amount=5, comment='testing inventory')

        p = self.api.get_product(id=4)
        self.assertEqual(p.stock, None)

    def test_limit_list_purchases(self):
        # check, if the objects are correct
        consumer = self.api.get_consumer(id=1)
        product = self.api.get_product(id=1)
        self.assertEqual(consumer.credit, 0)
        self.assertEqual(product.price, 25)

        pur = models.Purchase(consumer_id=1, product_id=1, amount=1,
                              comment="purchase done by unittest")
        self.api.insert_purchase(pur)
        pur = models.Purchase(consumer_id=1, product_id=1, amount=2,
                              comment="purchase done by unittest")
        self.api.insert_purchase(pur)
        pur = models.Purchase(consumer_id=1, product_id=1, amount=3,
                              comment="purchase done by unittest")
        self.api.insert_purchase(pur)
        pur = models.Purchase(consumer_id=1, product_id=1, amount=4,
                              comment="purchase done by unittest")
        self.api.insert_purchase(pur)

        # get all purchases
        purchases = self.api.list_purchases()
        self.assertEqual(len(purchases), 4)
        self.assertEqual(purchases[0].amount, 1)
        self.assertEqual(purchases[1].amount, 2)
        self.assertEqual(purchases[2].amount, 3)
        self.assertEqual(purchases[3].amount, 4)

        # get purchases with limit
        purchases = self.api.list_purchases(limit=2)
        self.assertEqual(len(purchases), 2)
        self.assertEqual(purchases[0].amount, 4)
        self.assertEqual(purchases[1].amount, 3)

    def test_update_purchase(self):
        # check, if the objects are correct
        consumer = self.api.get_consumer(id=1)
        product = self.api.get_product(id=1)
        self.assertEqual(consumer.credit, 0)
        self.assertEqual(product.price, 25)

        pur = models.Purchase(consumer_id=1, product_id=1, amount=5,
                              comment="purchase done by unittest")
        self.api.insert_purchase(pur)

        # check if the consumers credit has decreased
        pur = self.api.get_purchase(id=1)
        self.assertEqual(pur.comment, "purchase done by unittest")
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit,
                         0 - pur.amount * pur.paid_base_price_per_product
                         - pur.amount * pur.paid_karma_per_product)

        # revoke purchase and update comment
        pur = models.Purchase(id=1, revoked=True,
                              comment="purchases updated with unittest")
        self.api.update_purchase(pur)

        # check if the purchase has been updated
        pur2 = self.api.get_purchase(id=1)
        self.assertEqual(pur2.comment, "purchases updated with unittest")
        self.assertTrue(pur2.revoked)

        # do it twice to check whether it's indeponent
        with self.assertRaises(exc.CanOnlyBeRevokedOnce):
            self.api.update_purchase(pur)

        # check if the consumers credit has increased
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, 0)

        # this should do nothing
        pur = models.Purchase(id=1)
        self.api.update_purchase(pur)

        # check if the consumers credit is the same
        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, 0)

        # check non revocable products
        p = models.Product(name='Water', countable=False,
                           price=1, department_id=1, revocable=False)

        self.api.insert_product(p)

        pur = models.Purchase(consumer_id=1, product_id=4, amount=5,
                              comment="purchase done by unittest")
        self.api.insert_purchase(pur)

        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, -5)

        # revoke purchase and update comment
        pur = models.Purchase(id=2, revoked=True, comment="this should fail")
        with self.assertRaises(exc.NotRevocable):
            self.api.update_purchase(pur)

        consumer = self.api.get_consumer(id=1)
        self.assertEqual(consumer.credit, -5)

    def test_update_product(self):
        # define a shortcut to test the state of the product with id=1
        def check_product(name, price, active, stock, department_id):
            # check whether the product was inserted correctly
            prod = self.api.get_product(id=1)
            self.assertEqual(prod.name, name)
            self.assertEqual(prod.price, price)
            self.assertEqual(prod.active, active)
            self.assertEqual(prod.stock, stock)
            self.assertEqual(prod.department_id, department_id)

        # test update name
        prod3 = models.Product(id=1, name='Mars')
        self.api.update_product(prod3)
        check_product('Mars', 25, True, 0, 1)

        # test update active and stock
        prod4 = models.Product(id=1, active=False, stock=10)
        self.api.update_product(prod4)
        check_product('Mars', 25, False, 10, 1)

        # test update department_id
        prod4 = models.Product(id=1, department_id=2)
        self.api.update_product(prod4)
        check_product('Mars', 25, False, 10, 2)

        # test update price (negative prices are allowed!)
        prod5 = models.Product(id=1, price=-10)
        self.api.update_product(prod5)
        check_product('Mars', -10, False, 10, 2)

        # test update without id
        prod6 = models.Product(name="Rafaelo")
        with self.assertRaises(exc.FieldIsNone):
            self.api.update_product(prod6)
        # this should still be the same as before
        check_product('Mars', -10, False, 10, 2)

        # test update with unknown id
        prod7 = models.Product(id=5, name="Rafaelo")
        with self.assertRaises(exc.ObjectNotFound):
            self.api.update_product(prod7)
        # this should still be the same as before
        check_product('Mars', -10, False, 10, 2)

        # test update with duplicate name
        prod8 = models.Product(id=1, name="Pizza")
        with self.assertRaises(exc.DuplicateObject):
            self.api.update_product(prod8)
        # this should still be the same as before
        check_product('Mars', -10, False, 10, 2)

    def test_activities(self):
        # create and test workactivities
        workactivities = self.api.list_workactivities()
        self.assertEqual(len(workactivities), 0)

        workactivity = models.Workactivity(name="Getränke schleppen")
        self.api.insert_workactivity(workactivity)

        with self.assertRaises(exc.DuplicateObject):
            self.api.insert_workactivity(workactivity)

        workactivities = self.api.list_workactivities()
        self.assertEqual(len(workactivities), 1)

        workactivity = models.Workactivity(name="Skripte binden")
        self.api.insert_workactivity(workactivity)

        workactivities = self.api.list_workactivities()
        self.assertEqual(len(workactivities), 2)

        workactivity = models.Workactivity(id=1, name="Getränke hoch schleppen")
        self.api.update_workactivity(workactivity)

        workactivities = self.api.list_workactivities()
        self.assertEqual(workactivities[0].name, "Getränke hoch schleppen")
        self.assertEqual(workactivities[1].name, "Skripte binden")

        # create and test activities
        activities = self.api.list_activities()
        self.assertEqual(len(activities), 0)

        date1 = datetime.datetime.now() + datetime.timedelta(days=12)
        date2 = date1 + datetime.timedelta(days=12)

        activity = models.Activity(workactivity_id=1,
                                   date_deadline=date1,
                                   date_event=date2,
                                   created_by=1)

        self.api.insert_activity(activity)

        activities = self.api.list_activities()
        self.assertEqual(len(activities), 1)

        activity = models.Activity(workactivity_id=1,
                                   date_deadline=date1,
                                   date_event=date2,
                                   created_by=1)

        self.api.insert_activity(activity)

        activities = self.api.list_activities()
        self.assertEqual(len(activities), 2)

        delta = datetime.timedelta(days=1)

        activity = models.Activity(id=1, date_event=date2 + delta)
        self.api.update_activity(activity)

        # test activityfeedback

        activityfeedback = models.Activityfeedback(consumer_id=1,
                                                   activity_id=1,
                                                   feedback=True)
        self.api.insert_activityfeedback(activityfeedback)

        activityfeedback = models.Activityfeedback(consumer_id=1,
                                                   activity_id=1,
                                                   feedback=False)
        self.api.insert_activityfeedback(activityfeedback)

        activityfeedbacks = self.api.get_activityfeedback(activity_id=1)
        self.assertEqual(len(activityfeedbacks), 4)
        self.assertFalse(activityfeedbacks[1])
        self.assertEqual(activityfeedbacks[2], None)
        self.assertEqual(activityfeedbacks[3], None)
        self.assertEqual(activityfeedbacks[4], None)

        activityfeedbacks = self.api.get_activityfeedback(activity_id=1,
                                                          list_all=True)

        activityfeedback = models.Activityfeedback(consumer_id=2,
                                                   activity_id=1,
                                                   feedback=True)

        self.api.insert_activityfeedback(activityfeedback)

        activityfeedbacks = self.api.get_activityfeedback(activity_id=1,
                                                          list_all=True)

        self.assertEqual(len(activityfeedbacks), 4)
        self.assertEqual(len(activityfeedbacks[1]), 2)
        self.assertEqual(len(activityfeedbacks[2]), 1)
        self.assertTrue(activityfeedbacks[1][0]['feedback'])
        self.assertFalse(activityfeedbacks[1][1]['feedback'])
        self.assertTrue(activityfeedbacks[2][0]['feedback'])

        activityfeedback = models.Activityfeedback(consumer_id=1,
                                                   activity_id=1,
                                                   feedback=False)
        self.api.insert_activityfeedback(activityfeedback)

        # create activity

        date1 = datetime.datetime.now() + datetime.timedelta(milliseconds=1)
        date2 = date1 + datetime.timedelta(milliseconds=1)

        activity = models.Activity(workactivity_id=1,
                                   date_deadline=date1,
                                   date_event=date2,
                                   created_by=1)

        self.api.insert_activity(activity)

        time.sleep(0.01)
        activityfeedback = models.Activityfeedback(consumer_id=1,
                                                   activity_id=3,
                                                   feedback=False)

        with self.assertRaises(exc.InvalidDates):
            self.api.insert_activityfeedback(activityfeedback)
