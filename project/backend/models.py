#!/usr/bin/env python3

import datetime

from .validation import (GreaterOrEqual, LessOrEqual, MaxLength, MinLength,
                         Type, ValidatableObject, fields, SkipIfNone)


class Consumer(ValidatableObject):
    _tablename = 'consumers'
    _validators = {
        'id': [Type(int)],
        'name': [Type(str), MaxLength(64), MinLength(4)],
        'karma': [Type(int), GreaterOrEqual(-10), LessOrEqual(10)],
        'credit': [Type(int)],
        'isAdmin': [Type(bool)],
        'hasCredentials': [Type(bool)],
        'active': [Type(bool)],
        'email': [SkipIfNone(Type(str), MaxLength(256), MinLength(6))],
        'password': [SkipIfNone(Type(bytes), MaxLength(256), MinLength(6))],
        'studentnumber': [SkipIfNone(Type(int))]
    }


class Department(ValidatableObject):
    _tablename = 'departments'
    _validators = {
        'id': [Type(int)],
        'name': [Type(str), MaxLength(64), MinLength(4)],
        'income_base': [Type(int)],
        'income_karma': [Type(int)],
        'expenses': [Type(int)],
        'budget': [Type(int)]
    }


class PriceCategory(ValidatableObject):
    _tablename = 'pricecategories'
    _validators = {
        'id': [Type(int)],
        'price_lower_bound': [Type(int)],
        'additional_percent': [Type(int)]
    }


class Product(ValidatableObject):
    _tablename = 'products'
    _validators = {
        'id': [Type(int)],
        'name': [Type(str), MaxLength(64), MinLength(4)],
        'barcode': [SkipIfNone(Type(str), MaxLength(24), MinLength(4))],
        'price': [Type(int)],
        'department_id': [Type(int)],
        'active': [Type(bool)],
        'stock': [SkipIfNone(Type(int))],
        'countable': [Type(bool)],
        'revocable': [Type(bool)],
        'image': [SkipIfNone(Type(str), MaxLength(64), MinLength(4))]
    }


class Purchase(ValidatableObject):
    _tablename = 'purchases'
    _validators = {
        'id': [Type(int)],
        'consumer_id': [Type(int)],
        'product_id': [Type(int)],
        'amount': [Type(int)],
        'comment': [Type(str), MaxLength(64), MinLength(8)],
        'timestamp': [Type(datetime.datetime)],
        'revoked': [Type(bool)],
        'paid_base_price_per_product': [Type(int)],
        'paid_karma_per_product': [Type(int)]
    }


class Departmentpurchase(ValidatableObject):
    _tablename = 'departmentpurchases'
    _validators = {
        'id': [Type(int)],
        'timestamp': [Type(datetime.datetime)],
        'product_id': [Type(int)],
        'department_id': [Type(int)],
        'admin_id': [Type(int)],
        'amount': [Type(int)],
        'price_per_product': [Type(int)]
    }


class Deposit(ValidatableObject):
    _tablename = 'deposits'
    _validators = {
        'id': [Type(int)],
        'consumer_id': [Type(int)],
        'amount': [Type(int)],
        'comment': [Type(str), MaxLength(64), MinLength(8)],
        'timestamp': [Type(datetime.datetime)]
    }


class Payoff(ValidatableObject):
    _tablename = 'payoffs'
    _validators = {
        'id': [Type(int)],
        'admin_id': [Type(int)],
        'department_id': [Type(int)],
        'departmentpurchase_id': [SkipIfNone(Type(int))],
        'comment': [Type(str), MaxLength(64), MinLength(8)],
        'amount': [Type(int)],
        'revoked': [Type(bool)],
        'timestamp': [Type(datetime.datetime)]
    }


class Log(ValidatableObject):
    _tablename = 'logs'
    _validators = {
        'id': [Type(int)],
        'table_name': [Type(str), MaxLength(64), MinLength(4)],
        'updated_id': [Type(int)],
        'data_inserted': [Type(str), MaxLength(256), MinLength(4)],
        'timestamp': [Type(datetime.datetime)]
    }


class StockHistory(ValidatableObject):
    _tablename = 'stockhistory'
    _validators = {
        'id': [Type(int)],
        'product_id': [Type(int)],
        'new_stock': [Type(int)],
        'timestamp': [Type(datetime.datetime)]
    }


class AdminRole(ValidatableObject):
    _tablename = 'adminroles'
    _validators = {
        'id': [Type(int)],
        'consumer_id': [Type(int)],
        'department_id': [Type(int)],
        'timestamp': [Type(datetime.datetime)]
    }


class Bank(ValidatableObject):
    _tablename = 'banks'
    _validators = {
        'id': [Type(int)],
        'name': [Type(str), MaxLength(64), MinLength(4)],
        'credit': [Type(int)]
    }


class Workactivity(ValidatableObject):
    _tablename = 'workactivities'
    _validators = {
        'id': [Type(int)],
        'name': [Type(str), MaxLength(32), MinLength(4)]
    }


class Activity(ValidatableObject):
    _tablename = 'activities'
    _validators = {
        'id': [Type(int)],
        'created_by': [Type(int)],
        'reviewed': [Type(bool)],
        'workactivity_id': [Type(int)],
        'date_created': [Type(datetime.datetime)],
        'date_deadline': [Type(datetime.datetime)],
        'date_event': [Type(datetime.datetime)]
    }


class Activityfeedback(ValidatableObject):
    _tablename = 'activityfeedbacks'
    _validators = {
        'id': [Type(int)],
        'timestamp': [Type(datetime.datetime)],
        'consumer_id': [Type(int)],
        'activity_id': [Type(int)],
        'feedback': [Type(bool)]
    }
