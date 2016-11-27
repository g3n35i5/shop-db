#!/usr/bin/env python3

import unittest
from .validation import *


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
        with self.assertRaises(MaximumValueExceeded):
            self.test_obj.amount = 42
