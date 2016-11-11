#!/usr/bin/env python3

from validation import ValidatableObject, Type, fields


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