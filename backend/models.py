#!/usr/bin/env python3

import datetime

from .validation import (GreaterOrEqual, LessOrEqual, MaxLength, MinLength,
                         Type, ValidatableObject, fields)


def representation(obj):
    keys = list(fields(obj))
    keys.remove('id')

    r = ['<', type(obj).__name__, '(id=', str(obj.id)]

    for k in sorted(keys):
        v = getattr(obj, k)
        if type(v) is str:
            r.append(', {}="{}"'.format(k, v))
        else:
            r.append(', {}={}'.format(k, v))

    r.append(')>')

    return ''.join(r)


class Consumer(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'name': [Type(str), MaxLength(64), MinLength(4)],
        'karma': [Type(int), GreaterOrEqual(-10), LessOrEqual(10)],
        'credit': [Type(int)],
        'active': [Type(bool)]
    }

    def __repr__(self):
        return representation(self)


class Department(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'name': [Type(str), MaxLength(64), MinLength(4)],
        'income_base': [Type(int)],
        'income_karma': [Type(int)],
        'expenses': [Type(int)],
        'budget': [Type(int)]
    }

    def __repr__(self):
        return representation(self)


class KarmaScale(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'price_bound': [Type(int)],
        'additional_percent': [Type(int)]
    }

    def __repr__(self):
        return representation(self)


class Product(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'name': [Type(str), MaxLength(64), MinLength(4)],
        'price': [Type(int)],
        'department_id': [Type(int)],
        'active': [Type(bool)],
        'on_stock': [Type(bool)],
        'revocable': [Type(bool)]
    }

    def __repr__(self):
        return representation(self)


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

    def __repr__(self):
        return representation(self)


class Deposit(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'consumer_id': [Type(int)],
        'amount': [Type(int)],
        'comment': [Type(str), MaxLength(64), MinLength(8)],
        'timestamp': [Type(datetime.datetime)]
    }

    def __repr__(self):
        return representation(self)


class Payoff(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'department_id': [Type(int)],
        'comment': [Type(str), MaxLength(64), MinLength(8)],
        'amount': [Type(int)],
        'revoked': [Type(bool)],
        'timestamp': [Type(datetime.datetime)]
    }

    def __repr__(self):
        return representation(self)


class Log(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'table_name': [Type(str), MaxLength(64), MinLength(4)],
        'updated_id': [Type(int)],
        'data_inserted': [Type(str), MaxLength(256), MinLength(4)],
        'timestamp': [Type(datetime.datetime)]
    }

    def __repr__(self):
        return representation(self)


class Deed(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'name': [Type(str), MaxLength(64), MinLength(4)],
        'timestamp': [Type(datetime.datetime)],
        'done': [Type(bool)]
    }

    def __repr__(self):
        return representation(self)


class Participation(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'deed_id': [Type(int)],
        'consumer_id': [Type(int)],
        'flag_id': [Type(int)],
        'timestamp': [Type(datetime.datetime)]
    }

    def __repr__(self):
        return representation(self)


class Flag(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'name': [Type(str), MaxLength(64), MinLength(4)]
    }

    def __repr__(self):
        return representation(self)


class Bank(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'name': [Type(str), MaxLength(64), MinLength(4)],
        'credit': [Type(int)]
    }

    def __repr__(self):
        return representation(self)
