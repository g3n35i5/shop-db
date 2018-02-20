#!/usr/bin/env python3

import json
import project.backend.exceptions as exc


def fields(object):
    return object._validators.keys()


def to_dict(object):
    d = {}
    for f in fields(object):
        d[f] = getattr(object, f)
    return d


class LessThan(object):

    def __init__(self, other):
        self.other = other

    def validate(self, field, value):
        if value >= self.other:
            raise exc.MaximumValueExceeded(field, upper_bound=self.other)


class LessOrEqual(object):

    def __init__(self, other):
        self.other = other

    def validate(self, field, value):
        if value > self.other:
            raise exc.MaximumValueExceeded(field, upper_bound=self.other)


class GreaterThan(object):

    def __init__(self, other):
        self.other = other

    def validate(self, field, value):
        if value <= self.other:
            raise exc.MinimumValueUndershot(field, lower_bound=self.other)


class GreaterOrEqual(object):

    def __init__(self, other):
        self.other = other

    def validate(self, field, value):
        if value < self.other:
            raise exc.MinimumValueUndershot(field, lower_bound=self.other)


class MaxLength(object):

    def __init__(self, length):
        self.length = length

    def validate(self, field, value):
        if len(value) > self.length:
            raise exc.MaxLengthExceeded(field, max_allowed_length=self.length)


class MinLength(object):

    def __init__(self, length):
        self.length = length

    def validate(self, field, value):
        if len(value) < self.length:
            raise exc.MinLengthUndershot(field, min_allowed_length=self.length)


class Type(object):

    def __init__(self, type):
        self.type = type

    def validate(self, field, value):
        if type(value) is not self.type:
            raise exc.WrongType(field, expected_type=self.type.__name__)


class SkipIfNone(object):

    def __init__(self, *subvalidators):
        self.subvalidators = subvalidators

    def validate(self, field, value):
        if value is None:
            return

        for v in self.subvalidators:
            v.validate(field, value)


class ValidatableObject(object):

    def __init__(self, **kwargs):
        self._data = {}

        for k, v in kwargs.items():
            setattr(self, k, v)

    def __setattr__(self, field_name, field_value):
        if field_name in ['_data', '_validators']:
            self.__dict__[field_name] = field_value
            return

        field_validators = self._validators.get(field_name, None)

        if field_validators is None:
            raise exc.UnknownField(field_name)

        for v in field_validators:
            v.validate(field_name, field_value)

        self._data[field_name] = field_value

    def __getattr__(self, field_name):
        if field_name not in self._validators.keys():
            raise exc.UnknownField(field_name)

        return self._data.get(field_name, None)

    def __repr__(self):
        keys = list(fields(self))
        if 'id' in keys:
            del keys['id']
            _id = str(self.id)
        else:
            _id = 'None'

        representation = ['<', type(self).__name__, '(id=', _id]

        for k in sorted(keys):
            v = getattr(self, k)

            if type(v) is str:
                representation.append(', {}="{}"'.format(k, v))
            else:
                representation.append(', {}={}'.format(k, v))

        representation.append(')>')

        return ''.join(representation)
