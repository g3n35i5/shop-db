#!/usr/bin/env python3


class ValidationException(Exception):
    def __init__(self, field, value, **kwargs):
        self.field = field
        self.value = value
        self.kwargs = kwargs


class WrongType(ValidationException):
    def __str__(self):
        return 'The {} must be of type {}.' \
            .format(self.field, self.kwargs['expected_type'])


class MaxLengthExceeded(ValidationException):
    def __str__(self):
        return 'The {} "{}" exceeds the maximum allowed length of {}.' \
            .format(self.field,
                    getattr(self.object, self.field),
                    self.kwargs['max_length'])


class UnknownField(ValidationException):
    def __str__(self):
        return '{} is an unknown field.'.format(self.field)


class MaximumValueExceeded(ValidationException):
    def __str__(self):
        return '{} should be less than {}, but is {}.' \
            .format(self.field, self.kwargs['max_val'], self.value)


def fields(object):
    return object._validators.keys()


class LessThan(object):

    def __init__(self, other):
        self.other = other

    def validate(self, name, value):
        if value >= self.other:
            raise MaximumValueExceeded(name, value, max_val=self.other)


class MaxLength(object):
    def __init__(self, length):
        self.length = length

    def validate(self, name, value):
        if len(value) > self.length:
            raise MaxLengthExceeded(name, value, max_length=self.length)


class Type(object):

    def __init__(self, type):
        self.type = type

    def validate(self, name, value):
        if type(value) is not self.type:
            raise WrongType(name, value, expected_type=self.type)


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
            raise UnknownField(field_name, None)

        for v in field_validators:
            v.validate(field_name, field_value)

        self._data[field_name] = field_value

    def __getattr__(self, field_name):
        if field_name not in self._validators.keys():
            raise UnknownField(field_name, None)

        return self._data.get(field_name, None)
