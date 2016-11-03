#!/usr/bin/env python3

import unittest


class WrongType(Exception):
    pass


class MaxLengthExceeded(Exception):
    pass


class UnknownField(Exception):
    pass


class LessThan(object):

    def __init__(self, other):
        self.other = other

    def validate(self, name, value):
        if value >= self.other:
            raise Exception(
                'Field {} should be less than {}, but is {}'
                .format(name, self.other, value)
            )


class MaxLength(object):
    def __init__(self, length):
        self.length = length

    def validate(self, name, value):
        if len(value) > self.length:
            raise MaxLengthExceeded(
                'String {} should of length {}, but is {}'
                .format(name, self.length, len(value)))


class Type(object):

    def __init__(self, type):
        self.type = type

    def validate(self, name, value):
        if type(value) is not self.type:
            raise WrongType(
                'Field {} should be of type {}'.format(name, self.type)
            )


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
            # TODO: add class name to message
            raise UnknownField('Field {} is unknown'.format(field_name))

        for v in field_validators:
            v.validate(field_name, field_value)

        self._data[field_name] = field_value

    def __getattr__(self, field_name):
        if field_name not in self._validators.keys():
            # TODO: add class name to message
            raise UnknownField('Field {} is unknown'.format(field_name))

        return self._data.get(field_name, None)


class TestValidatableObject(unittest.TestCase):

    def setUp(self):
        class TestClass(ValidatableObject):
            _validators = {
                'name': [Type(str), MaxLength(20)],
                'amount': [Type(int), LessThan(5)]
            }

        self.test_obj = TestClass()

    def test_string_too_long(self):
        with self.assertRaises(MaxLengthExceeded):
            self.test_obj.name = "thisfieldismuchtoolong"

    def test_set_unknown_field(self):
        with self.assertRaises(UnknownField):
            self.test_obj.foo = 'bar'

    def test_get_unknown_field(self):
        with self.assertRaises(UnknownField):
            print(self.test_obj.foo)

    def test_set_wrong_type_int(self):
        with self.assertRaises(WrongType):
            self.test_obj.amount = 'banane'

    def test_set_int(self):
        self.test_obj.amount = 2

    def test_set_wrong_type_string(self):
        with self.assertRaises(WrongType):
            self.test_obj.name = 2

    def test_set_string(self):
        self.test_obj.name = 'banane'

    def test_less_than_exception(self):
        with self.assertRaises(Exception):
            self.test_obj.amount = 42
