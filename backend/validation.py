#!/usr/bin/env python3


class WrongType(Exception):
    pass


class MaxLengthExceeded(Exception):
    pass


class UnknownField(Exception):
    pass


def fields(object):
    return object._validators.keys()


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
