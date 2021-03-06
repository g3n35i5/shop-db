#!/usr/bin/env python3


class AuthenticationException(Exception):

    def __init__(self, **kwargs):
        self.info = kwargs


class NotResponsible(AuthenticationException):

    def __init__(self):
        AuthenticationException.__init__(self)


class NotAuthorized(AuthenticationException):

    def __init__(self):
        AuthenticationException.__init__(self)


class TokenMissing(AuthenticationException):

    def __init__(self):
        AuthenticationException.__init__(self)


class TokenInvalid(AuthenticationException):

    def __init__(self):
        AuthenticationException.__init__(self)


class PasswordsDoNotMatch(AuthenticationException):

    def __init__(self):
        AuthenticationException.__init__(self)


class ConsumerNeedsCredentials(AuthenticationException):

    def __init__(self):
        InputException.__init__(self)


class InputException(Exception):

    def __init__(self, **kwargs):
        self.info = kwargs


class NothingHasChanged(InputException):

    def __init__(self):
        InputException.__init__(self)


class ObjectNotFound(InputException):

    def __init__(self):
        InputException.__init__(self)


class InvalidDepartmentpurchase(InputException):

    def __init__(self):
        InputException.__init__(self)


class FieldBasedException(InputException):

    def __init__(self, field, **kwargs):
        InputException.__init__(self, field=field, **kwargs)


class InvalidJSON(InputException):
    def __init__(self):
        InputException.__init__(self)


class MissingData(InputException):
    def __init__(self):
        InputException.__init__(self)


class WrongType(FieldBasedException):

    def __init__(self, field, expected_type):
        FieldBasedException.__init__(self, field, expected_type=expected_type)


class MaxLengthExceeded(FieldBasedException):

    def __init__(self, field, max_allowed_length):
        FieldBasedException.__init__(self, field,
                                     max_allowed_length=max_allowed_length)


class MinLengthUndershot(FieldBasedException):

    def __init__(self, field, min_allowed_length):
        FieldBasedException.__init__(self, field,
                                     min_allowed_length=min_allowed_length)


class UnknownField(FieldBasedException):

    def __init__(self, field):
        FieldBasedException.__init__(self, field)


class MaximumValueExceeded(FieldBasedException):

    def __init__(self, field, upper_bound):
        FieldBasedException.__init__(self, field, upper_bound=upper_bound)


class MinimumValueUndershot(FieldBasedException):

    def __init__(self, field, lower_bound):
        FieldBasedException.__init__(self, field, lower_bound=lower_bound)


class ForeignKeyNotExisting(FieldBasedException):

    def __init__(self, field):
        FieldBasedException.__init__(self, field)


class FieldIsNone(FieldBasedException):

    def __init__(self, field):
        FieldBasedException.__init__(self, field)


class ForbiddenField(FieldBasedException):

    def __init__(self, field):
        FieldBasedException.__init__(self, field)


class InvalidDates(FieldBasedException):

    def __init__(self):
        InputException.__init__(self)


class OnlyOneRowAllowed(FieldBasedException):

    def __init__(self):
        InputException.__init__(self)


class ProductNotCountable(FieldBasedException):

    def __init__(self):
        InputException.__init__(self)


class DuplicateObject(FieldBasedException):

    def __init__(self, field):
        FieldBasedException.__init__(self, field)


class CanOnlyBeRevokedOnce(FieldBasedException):

    def __init__(self):
        FieldBasedException.__init__(self, 'revoked')


class RevokeIsFinal(FieldBasedException):

    def __init__(self):
        FieldBasedException.__init__(self, 'revoked')


class NotRevocable(FieldBasedException):

    def __init__(self, product):
        FieldBasedException.__init__(self, product.name)


exception_mapping = {
    MissingData:
    {
        "types": ["input-exception",
                  "missing-data"],
        "code": 400
    },
    NotAuthorized:
    {
        "types": ["authentication-exception",
                  "not-authorized"],
        "code": 403
    },
    TokenMissing:
    {
        "types": ["authentication-exception",
                  "token-missing"],
        "code": 403
    },
    TokenInvalid:
    {
        "types": ["authentication-exception",
                  "token-invalid"],
        "code": 403
    },
    PasswordsDoNotMatch:
    {
        "types": ["authentication-exception",
                  "passwords-do-not-match"],
        "code": 400
    },
    ConsumerNeedsCredentials:
    {
        "types": ["authentication-exception",
                  "consumer-needs-credentials"],
        "code": 400
    },
    NotResponsible:
    {
        "types": ["authentication-exception",
                  "not-responsible"],
        "code": 403
    },
    WrongType:
    {
        "types": ["input-exception",
                  "field-based-exception",
                  "wrong-type"],
        "code": 400
    },
    MaxLengthExceeded:
    {
        "types": ["input-exception",
                  "field-based-exception",
                  "max-length-exceeded"],
        "code": 400
    },
    MinLengthUndershot:
    {
        "types": ["input-exception",
                  "field-based-exception",
                  "min-length-undercut"],
        "code": 400
    },
    UnknownField:
    {
        "types": ["input-exception",
                  "field-based-exception",
                  "unknown-field"],
        "code": 400
    },
    MaximumValueExceeded:
    {
        "types": ["input-exception",
                  "field-based-exception",
                  "maximum-value-exceeded"],
        "code": 400
    },
    InvalidJSON:
    {
        "types": ["input-exception", "invalid-json"],
        "code": 400
    },
    DuplicateObject:
    {
        "types": ["input-exception",
                  "field-based-exception",
                  "duplicate-object"],
        "code": 400
    },
    ForeignKeyNotExisting:
    {
        "types": ["input-exception",
                  "field-based-exception",
                  "foreign-key-not-existing"],
        "code": 400
    },
    FieldIsNone:
    {
        "types": ["input-exception",
                  "field-based-exception",
                  "field-is-none"],
        "code": 400
    },
    ForbiddenField:
    {
        "types": ["input-exception",
                  "field-based-exception",
                  "forbidden-field"],
        "code": 400
    },
    ObjectNotFound:
    {
        "types": ["input-exception",
                  "object-not-found"],
        "code": 404
    },
    DuplicateObject:
    {
        "types": ["input-exception",
                  "field-based-exception",
                  "duplicate-object"],
        "code": 400
    },
    CanOnlyBeRevokedOnce:
    {
        "types": ["input-exception",
                  "field-based-exception",
                  "can-only-be-revoked-once"],
        "code": 400
    },
    RevokeIsFinal:
    {
        "types": ["input-exception",
                  "field-based-exception",
                  "revoke-is-final"],
        "code": 400
    },
    NothingHasChanged:
    {
        "types": ["input-exception",
                  "nothing-has-changed"],
        "code": 200
    },
    InvalidDepartmentpurchase:
    {
        "types": ["input-exception",
                  "invalid-departmentpurchase"],
        "code": 400
    }
}
