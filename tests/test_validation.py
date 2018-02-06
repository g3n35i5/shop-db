#!/usr/bin/env python3

from base import BaseTestCase
from project.backend.validation import *

class ValidationTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        class TestClass(ValidatableObject):
            _validators = {
                'name': [Type(str), MaxLength(20), MinLength(4)],
                'amount': [Type(int), LessThan(5)],
                'canbenone': [SkipIfNone(Type(str))]
            }

        self.test_obj = TestClass()

    def test_can_be_none(self):
        self.test_obj.canbenone = None
        self.test_obj.canbenone = 'Can be a string'

    def test_string_too_long(self):
        with self.assertRaises(MaxLengthExceeded):
            self.test_obj.name = "thisfieldismuchtoolong"

    def test_string_too_short(self):
        with self.assertRaises(MinLengthUndershot):
            self.test_obj.name = "abc"

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
