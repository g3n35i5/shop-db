#!/usr/bin/env python3

from .validation import ValidatableObject, Type, fields
import datetime


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
        'name': [Type(str)],
        'credit': [Type(int)],
        'active': [Type(bool)]
    }

    def __repr__(self):
        return representation(self)


class Product(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'name': [Type(str)],
        'price': [Type(int)],
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
        'timestamp': [Type(datetime.datetime)],
        'revoked': [Type(bool)],
        'paid_price': [Type(int)]
    }

    def __repr__(self):
        return representation(self)


class Deposit(ValidatableObject):
    _validators = {
        'id': [Type(int)],
        'consumer_id': [Type(int)],
        'timestamp': [Type(datetime.datetime)],
        'amount': [Type(int)]
    }

    def __repr__(self):
        return representation(self)