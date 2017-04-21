#!/usr/bin/env python3

import datetime

from .validation import MaxLength, MinLength, Type, ValidatableObject, fields


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
        'credit': [Type(int)],
        'active': [Type(bool)]
    }

    def __repr__(self):
        return representation(self)


class Department(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'name': [Type(str), MaxLength(64), MinLength(4)],
        'income': [Type(int)],
        'expenses': [Type(int)],
        'budget': [Type(int)]
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
        'on_stock': [Type(bool)]
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
        'paid_price_per_product': [Type(int)]
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
        'bank_id': [Type(int)],
        'department_id': [Type(int)],
        'comment': [Type(str), MaxLength(64), MinLength(8)],
        'amount': [Type(int)],
        'timestamp': [Type(datetime.datetime)]
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
