#!/usr/bin/python3
import json
import sqlite3

from flask import Flask, Request, g, jsonify, request
from flask_cors import CORS
from werkzeug.local import LocalProxy

from backend.db_api import (DatabaseApi, DuplicateObject, FieldIsNone,
                            ForbiddenField, ForeignKeyNotExisting,
                            ObjectNotFound, PurchaseCanOnlyBeRevokedOnce)
from backend.models import Consumer, Deposit, Product, Purchase
from backend.validation import (FieldBasedException, InputException,
                                MaximumValueExceeded, MaxLengthExceeded,
                                UnknownField, WrongType, to_dict)

app = Flask(__name__)

CORS(app)


def get_api():
    api = getattr(g, '_api', None)
    if api is None:
        db = sqlite3.connect('shop.db', detect_types=sqlite3.PARSE_DECLTYPES)
        api = g._api = DatabaseApi(db)
    return api

api = LocalProxy(get_api)


@app.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


class InvalidJSON(InputException):
    pass


def handle_json_error(self, e):
    raise InvalidJSON()

Request.on_json_loading_failed = handle_json_error


@app.errorhandler(404)
def not_found(error):
    return jsonify(types=["resource-not-found"]), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify(types=["internal-server-error"], info="Please contact the admin!"), 500


exception_mapping = {
    WrongType: {"types": ["input-exception", "field-based-exception", "wrong-type"], "code": 400},
    MaxLengthExceeded: {"types": ["input-exception", "field-based-exception", "max-length-exceeded"], "code": 400},
    UnknownField: {"types": ["input-exception", "field-based-exception", "unknown-field"], "code": 400},
    MaximumValueExceeded: {"types": ["input-exception", "field-based-exception", "maximum-value-exceeded"], "code": 400},
    InvalidJSON: {"types": ["input-exception", "invalid-json"], "code": 400},
    DuplicateObject: {"types": ["input-exception", "field-based-exception", "duplicate-object"], "code": 400},
    ForeignKeyNotExisting: {"types": ["input-exception", "field-based-exception", "foreign-key-not-existing"], "code": 400},
    FieldIsNone: {"types": ["input-exception", "field-based-exception", "field-is-none"], "code": 400},
    ForbiddenField: {"types": ["input-exception", "field-based-exception", "forbidden-field"], "code": 400},
    # TODO: field based?
    ObjectNotFound: {"types": ["input-exception", "object-not-found"], "code": 404},
    DuplicateObject: {"types": ["input-exception", "field-based-exception", "duplicate-object"], "code": 400},
    PurchaseCanOnlyBeRevokedOnce: {"types": [
        "input-exception", "field-based-exception", "purchase-can-only-be-revoked-once"], "code": 400}
}


@app.errorhandler(Exception)
def handle_error(e):
    if type(e) in exception_mapping:
        foo = exception_mapping[type(e)]
        # TODO: json content type?

        return jsonify(
            result='error',
            code=foo['code'],
            error_types=foo['types'],
            info=e.info
        ), foo['code']
    else:
        raise e


@app.route('/consumers', methods=['GET'])
def list_consumers():
    return jsonify(list(map(to_dict, api.list_consumers())))


@app.route('/consumers', methods=['POST'])
def create_consumer():
    c = Consumer(**request.get_json())
    api.insert_consumer(c)
    return jsonify(result='created'), 201


@app.route('/consumers/<int:id>', methods=['GET'])
def get_consumer(id):
    return jsonify(to_dict(api.get_consumer(id)))


@app.route('/consumers/<int:id>', methods=['PUT'])
def put_consumer(id):
    c = Consumer(**request.get_json())
    c.id = id
    api.update_consumer(c)
    return jsonify(result='updated'), 200  # TODO: another status code?


@app.route('/products', methods=['GET'])
def list_products():
    return jsonify(list(map(to_dict, api.list_products())))


@app.route('/products', methods=['POST'])
def create_product():
    p = Product(**request.get_json())
    api.insert_product(p)
    return jsonify(result='created'), 201


@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    return jsonify(to_dict(api.get_product(id)))


@app.route('/products/<int:id>', methods=['PUT'])
def put_product(id):
    p = Product(**request.get_json())
    p.id = id
    api.update_product(p)
    return jsonify(result='updated'), 200


@app.route('/purchases', methods=['GET'])
def list_purchases():
    return jsonify(list(map(to_dict, api.list_purchases())))


@app.route('/purchases', methods=['POST'])
def create_purchase():
    p = Purchase(**request.get_json())
    api.insert_purchase(p)
    return jsonify(result='created'), 201


@app.route('/purchases/<int:id>', methods=['GET'])
def get_purchase(id):
    return jsonify(to_dict(api.get_purchase(id)))


@app.route('/purchases/<int:id>', methods=['PUT'])
def put_purchase(id):
    p = Purchase(**request.get_json())
    p.id = id
    api.update_purchase(p)
    return jsonify(result='updated'), 200


@app.route('/deposits', methods=['GET'])
def list_deposits():
    return jsonify(list(map(to_dict, api.list_deposits())))


@app.route('/deposits', methods=['POST'])
def create_deposit():
    d = Deposit(**request.get_json())
    api.insert_deposit(d)
    return jsonify(result='created'), 201
