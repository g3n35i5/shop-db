#!/usr/bin/env python3

import datetime

from .validation import (GreaterOrEqual, LessOrEqual, MaxLength, MinLength,
                         Type, ValidatableObject, fields, SkipIfNone)


class Information(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'version_major': [Type(int)],
        'version_minor': [Type(int)],
        'use_karma': [Type(bool)]
    }


class Consumer(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'name': [Type(str), MaxLength(64), MinLength(4)],
        'karma': [Type(int), GreaterOrEqual(-10), LessOrEqual(10)],
        'credit': [Type(int)],
        'active': [Type(bool)]
    }


class Department(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'name': [Type(str), MaxLength(64), MinLength(4)],
        'income_base': [Type(int)],
        'income_karma': [Type(int)],
        'expenses': [Type(int)],
        'budget': [Type(int)]
    }


class PriceCategory(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'price_lower_bound': [Type(int)],
        'additional_percent': [Type(int)]
    }


class Product(ValidatableObject):
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
        'image': [Type(str), MaxLength(64), MinLength(4)]
    }


class Purchase(ValidatableObject):
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


class Deposit(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'consumer_id': [Type(int)],
        'amount': [Type(int)],
        'comment': [Type(str), MaxLength(64), MinLength(8)],
        'timestamp': [Type(datetime.datetime)]
    }


class Payoff(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'department_id': [Type(int)],
        'comment': [Type(str), MaxLength(64), MinLength(8)],
        'amount': [Type(int)],
        'revoked': [Type(bool)],
        'timestamp': [Type(datetime.datetime)]
    }


class Log(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'table_name': [Type(str), MaxLength(64), MinLength(4)],
        'updated_id': [Type(int)],
        'data_inserted': [Type(str), MaxLength(256), MinLength(4)],
        'timestamp': [Type(datetime.datetime)]
    }


class StockHistory(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'product_id': [Type(int)],
        'new_stock': [Type(int)],
        'timestamp': [Type(datetime.datetime)]
    }


    _validators = {
        'id': [Type(int)],
        'timestamp': [Type(datetime.datetime)]
    }


    _validators = {
        'id': [Type(int)],
    }


class Bank(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'name': [Type(str), MaxLength(64), MinLength(4)],
        'credit': [Type(int)]
    }
