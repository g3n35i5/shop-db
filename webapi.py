#!/usr/bin/python3
import json
import logging
import pdb
import sqlite3
from logging.handlers import RotatingFileHandler
import datetime

from flask import Flask, Request, g, jsonify, request, make_response
import jwt
from functools import wraps
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from werkzeug.local import LocalProxy

from backend.db_api import (CanOnlyBeRevokedOnce, DatabaseApi, DuplicateObject,
                            FieldIsNone, ForbiddenField, ForeignKeyNotExisting,
                            ObjectNotFound)
from backend.models import (Consumer, Deposit, Information, Payoff, Product,
                            Purchase)
from backend.validation import (FieldBasedException, InputException,
                                MaximumValueExceeded, MaxLengthExceeded,
                                MinLengthUndershot, UnknownField, WrongType,
                                to_dict)

app = Flask(__name__)
app.config['adminName'] = 'admin'
app.config['adminPassword'] = 'admin'
app.config['SECRET_KEY'] = 'supersecretkey'


CORS(app)

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


def json_body():
    jb = request.get_json()
    if jb is None:
        raise InvalidJSON()
    return jb


exception_mapping = {
    WrongType: {"types": ["input-exception", "field-based-exception", "wrong-type"], "code": 400},
    MaxLengthExceeded: {"types": ["input-exception", "field-based-exception", "max-length-exceeded"], "code": 400},
    MinLengthUndershot: {"types": ["input-exception", "field-based-exception", "min-length-undercut"], "code": 400},
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
    CanOnlyBeRevokedOnce: {"types": [
        "input-exception", "field-based-exception", "can-only-be-revoked-once"], "code": 400}
}


def tokenRequired(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'token' in request.headers:
            token = request.headers['token']

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(*args, **kwargs)
    return decorated


@app.errorhandler(Exception)
def handle_error(e):
    if type(e) in exception_mapping:
        foo = exception_mapping[type(e)]
        # TODO: json content type?
        app.logger.warning('errorcode {} error_types {}'.format(
            foo['code'], foo['types']))

        return jsonify(
            result='error',
            code=foo['code'],
            error_types=foo['types'],
            info=e.info
        ), foo['code']
    else:
        app.logger.error('ERROR: {}'.format(e))
        raise e


@app.route('/status', methods=['GET'])
def getStatus():
    return jsonify(result=True), 200

@app.route('/login', methods=['POST'])
def login():
    try:
        json_data = request.json
        username = json_data['email']
        password = json_data['password']
    except:
        return make_response('Could not verify', 401)

    if username == app.config['adminName'] and password == app.config['adminPassword']:
        token = jwt.encode(
            {
            'user': 'Admin',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
            }, app.config['SECRET_KEY'])
    else:
        return make_response('Could not verify', 401)

    admin = {}
    admin['name'] = 'Admin'
    departments = list(map(to_dict, api.list_departments()))
    adminroles = []
    for d in departments:
        a = {}
        a['department_id'] = d['id']
        adminroles.append(a)

    admin['adminroles'] = adminroles

    return jsonify({'result': True, 'admin': admin, 'token': token.decode('UTF-8')})


@app.route('/consumers', methods=['GET'])
def list_consumers():
    return jsonify(list(map(to_dict, api.list_consumers())))


@app.route('/departments', methods=['GET'])
def list_departments():
    return jsonify(list(map(to_dict, api.list_departments())))


@app.route('/consumers', methods=['POST'])
@tokenRequired
def create_consumer():
    c = Consumer(**json_body())
    api.insert_consumer(c)
    app.logger.info('created consumer: {}'.format(c))
    return jsonify(result='created'), 201


@app.route('/consumer/<int:id>', methods=['GET'])
def get_consumer(id):
    return jsonify(to_dict(api.get_consumer(id)))


@app.route('/consumers/<int:id>', methods=['PUT'])
@tokenRequired
def put_consumer(id):
    if 'credit' in json_body():
        del json_body()['credit']
    c = Consumer(**json_body())
    c.id = id
    api.update_consumer(c)
    app.logger.info('updated consumer: {}'.format(c))
    return jsonify(result='updated'), 200  # TODO: another status code?


@app.route('/consumer/<int:id>/purchases', methods=['GET'])
def get_consumer_purchases(id):
    return jsonify(list(map(to_dict, api.get_purchases_of_consumer(id))))


@app.route('/consumer/<int:id>/deposits', methods=['GET'])
def get_consumer_deposits(id):
    return jsonify(list(map(to_dict, api.get_deposits_of_consumer(id))))


@app.route('/products', methods=['GET'])
def list_products():
    app.logger.warning('listing products')
    return jsonify(list(map(to_dict, api.list_products())))


@app.route('/favorites/<int:id>', methods=['GET'])
def get_favorite_products(id):
    app.logger.warning('listing favorites')
    return jsonify(list(map(to_dict, api.get_favorite_products(id))))


@app.route('/products', methods=['POST'])
@tokenRequired
def create_product():
    p = Product(**json_body())
    api.insert_product(p)
    app.logger.warning('created product: {}'.format(p))
    return jsonify(result='created'), 201


@app.route('/product/<int:id>', methods=['GET'])
def get_product(id):
    return jsonify(to_dict(api.get_product(id)))


@app.route('/products/<int:id>', methods=['PUT'])
@tokenRequired
def put_product(id):
    p = Product(**json_body())
    p.id = id
    api.update_product(p)
    app.logger.warning('updated product: {}'.format(p))
    return jsonify(result='updated'), 200


@app.route('/purchases', methods=['GET'])
def list_purchases():
    return jsonify(list(map(to_dict, api.list_purchases())))


@app.route('/purchases/<int:limit>', methods=['GET'])
def get_purchases_limit(limit):
    return jsonify(list(map(to_dict, api.list_purchases(limit=limit))))


@app.route('/purchases', methods=['POST'])
def create_purchase():
    p = Purchase(**json_body())
    api.insert_purchase(p)
    app.logger.warning('purchase created {}'.format(p))
    return jsonify(result='created'), 201


@app.route('/purchase/<int:id>', methods=['GET'])
def get_purchase(id):
    return jsonify(to_dict(api.get_purchase(id)))


@app.route('/purchases/<int:id>', methods=['PUT'])
def put_purchase(id):
    p = Purchase(**json_body())
    p.id = id
    api.update_purchase(p)
    app.logger.warning('updated purchase: {}'.format(p))
    return jsonify(result='updated'), 200


@app.route('/deposits', methods=['GET'])
def list_deposits():
    return jsonify(list(map(to_dict, api.list_deposits())))


@app.route('/deposits/<int:limit>', methods=['GET'])
def get_deposits_limit(limit):
    return jsonify(list(map(to_dict, api.list_deposits(limit=limit))))


@app.route('/deposits', methods=['POST'])
@tokenRequired
def create_deposit():
    d = Deposit(**json_body())
    api.insert_deposit(d)
    app.logger.warning('created deposit: {}'.format(d))
    return jsonify(result='created'), 201


@app.route('/statistics/department/<int:id>', methods=['GET'])
@tokenRequired
def getDepartmentStatistics(id):
    return jsonify(api.getDepartmentStatistics(id))


@app.route('/stockhistory/<int:id>', methods=['GET'])
def get_stockhistory(id):
    try:
        json_data = request.json
        date_start = json_data['date_start']
        date_end = json_data['date_end']
    except KeyError:
        date_start = None
        date_end = None

    sh = api.get_stockhistory(product_id=product_id,
                              date_start=date_start,
                              date_end=date_end)

    return jsonify(list(map(to_dict, sh)))


@app.route('/information', methods=['GET'])
def get_backend_information():
    return jsonify(to_dict(api.list_information()[0]))


@app.route('/information', methods=['PUT'])
@tokenRequired
def update_information(id):
    i = Information(**json_body())
    i.id = 1
    api.update_information(i)
    app.logger.warning('updated information: {}'.format(i))
    return jsonify(result='updated'), 200


@app.route('/top_products/<int:num_products>', methods=['GET'])
def get_top_products(num_products):
    return jsonify(api.get_top_products(num_products=num_products))


@app.route('/payoff', methods=['POST'])
@tokenRequired
def insert_payoff():
    p = Payoff(**json_body())
    api.insert_payoff(p)
    app.logger.warning('created payoff: {}'.format(p))
    return jsonify(result='created'), 201

@app.route('/payoffs', methods=['GET'])
def list_payoffs():
    return jsonify(list(map(to_dict, api.list_payoffs())))

if __name__ == "__main__":
    handler = RotatingFileHandler('backend.log', maxBytes=60000, backupCount=1)
    handler.setLevel(logging.DEBUG)
    app.logger.addHandler(handler)
    app.run(host="0.0.0.0")
