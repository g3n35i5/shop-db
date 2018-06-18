#!/usr/bin/env python3

from base import BaseTestCase
from project.backend.validation import *
import project.backend.exceptions as exc


class ValidationTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

        class TestClass(ValidatableObject):
            _validators = {
                'name': [Type(str), MaxLength(20), MinLength(4)],
                'amount': [Type(int), LessThan(5), GreaterThan(1)],
                'age': [Type(int), GreaterOrEqual(0), LessOrEqual(99)],
                'canbenone': [SkipIfNone(Type(str))]
            }

        self.test_obj = TestClass()

    def test_can_be_none(self):
        self.test_obj.canbenone = None
        self.test_obj.canbenone = 'Can be a string'

    def test_string_too_long(self):
        with self.assertRaises(exc.MaxLengthExceeded):
            self.test_obj.name = "thisfieldismuchtoolong"

    def test_string_too_short(self):
        with self.assertRaises(exc.MinLengthUndershot):
            self.test_obj.name = "abc"

    def test_set_unknown_field(self):
        with self.assertRaises(exc.UnknownField):
            self.test_obj.foo = 'bar'

    def test_get_unknown_field(self):
        with self.assertRaises(exc.UnknownField):
            print(self.test_obj.foo)

    def test_set_wrong_type_int(self):
        with self.assertRaises(exc.WrongType):
            self.test_obj.amount = 'banane'

    def test_set_int(self):
        self.test_obj.amount = 2

    def test_greater_than(self):
        with self.assertRaises(exc.MinimumValueUndershot):
            self.test_obj.amount = 1

    def test_less_or_equal(self):
        with self.assertRaises(exc.MaximumValueExceeded):
            self.test_obj.age = 100

    def test_greater_or_equal(self):
        with self.assertRaises(exc.MinimumValueUndershot):
            self.test_obj.age = -2

    def test_set_wrong_type_string(self):
        with self.assertRaises(exc.WrongType):
            self.test_obj.name = 2

    def test_set_string(self):
        self.test_obj.name = 'banane'

    def test_less_than_exception(self):
        with self.assertRaises(exc.MaximumValueExceeded):
            self.test_obj.amount = 42

    def test_representation(self):
        self.test_obj.name = 'test'
        self.test_obj.amount = 2
        self.test_obj.age = 9
        self.test_obj.canbenone = None
        b = '<TestClass(id=None, age=9, amount=2, canbenone=None, name="test")>'
        self.assertEqual(str(self.test_obj), b)
