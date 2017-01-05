#!/usr/bin/env python3

import json


class FieldBasedException(Exception):
    type = 'field-based'

    def __init__(self, field, **kwargs):
        self.field = field
        self.kwargs = kwargs


class WrongType(FieldBasedException):
    def __str__(self):
        return ('The {0.field} must be of type {expected_type.__name__}.'
                .format(self, **self.kwargs))


class MaxLengthExceeded(FieldBasedException):
    def __str__(self):
        return ('Maximum allowed length for {0.field} is {max_length}.'
                .format(self, **self.kwargs))


class UnknownField(FieldBasedException):
    def __str__(self):
        return '{0.field} is an unknown field.'.format(self)


class MaximumValueExceeded(FieldBasedException):
    def __str__(self):
        return ('{0.field} has to be less than {max_val}, but is {value}.'
                .format(self, **self.kwargs))


def fields(object):
    return object._validators.keys()


def to_dict(object):
    d = {}
    for f in fields(object):
        d[f] = getattr(object, f)
    return d


def to_json(converable):
    if type(converable) is list:
        return json.dumps([to_dict(obj) for obj in converable])
    else:
        return json.dumps(to_dict(converable))


class LessThan(object):

    def __init__(self, other):
        self.other = other

    def validate(self, field, value):
        if value >= self.other:
            raise MaximumValueExceeded(field, value=value, max_val=self.other)


class MaxLength(object):
    def __init__(self, length):
        self.length = length

    def validate(self, field, value):
        if len(value) > self.length:
            raise MaxLengthExceeded(field, value=value, max_length=self.length)


class Type(object):

    def __init__(self, type):
        self.type = type

    def validate(self, field, value):
        if type(value) is not self.type:
            raise WrongType(field, value=value, expected_type=self.type)


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
            raise UnknownField(field_name)

        for v in field_validators:
            v.validate(field_name, field_value)

        self._data[field_name] = field_value

    def __getattr__(self, field_name):
        if field_name not in self._validators.keys():
            raise UnknownField(field_name)

        return self._data.get(field_name, None)
