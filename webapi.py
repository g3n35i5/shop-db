#!/usr/bin/env python3
import json
import pdb
import sqlite3
import datetime

from flask import Flask, Request, g, jsonify, request, make_response
from flask_bcrypt import Bcrypt
import jwt
from functools import wraps
from flask_cors import CORS
from werkzeug.local import LocalProxy
import configuration as config

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
app.config.from_object(config.DevelopmentConfig)
bcrypt = Bcrypt(app)
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

def tokenOptional(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'token' in request.headers:
            token = request.headers['token']

        if not token:
            return f(False, *args, **kwargs)

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
        except:
            return f(False, *args, **kwargs)

        return f(True, *args, **kwargs)
    return decorated

def convertMinimal(_list, _fields):
    out = []
    for item in _list:
        element = {}
        for field in _fields:
            element[field] = getattr(item, field)

        out.append(element)

    return out

@app.errorhandler(Exception)
def handle_error(e):
    return e
    if type(e) in exception_mapping:
        foo = exception_mapping[type(e)]
        return jsonify(
            result='error',
            code=foo['code'],
            error_types=foo['types'],
            info=e.info
        ), foo['code']
    else:
        raise e




############################### Backend Status ################################

@app.route('/status', methods=['GET'])
def getStatus():
    return jsonify(result=True), 200




############################### Login #########################################

@app.route('/login', methods=['POST'])
def login():
    try:
        json_data = request.json
        email = json_data['email']
        password = json_data['password']
    except:
        return make_response('Could not verify', 401)

    try:
        consumer = to_dict(api.get_consumer_by_email(email))
    except:
        return make_response('Could not verify', 401)

    try:
        if bcrypt.check_password_hash(consumer['password'], password):
            del consumer['password']
            exp = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
            token = jwt.encode(
                {
                    'exp': exp
                }, app.config['SECRET_KEY'])
        else:
            return make_response('Could not verify', 401)
    except:
        return make_response('Could not verify', 401)

    departments = list(map(to_dict, api.list_departments()))
    adminroles = []
    for d in departments:
        a = {}
        a['department_id'] = d['id']
        adminroles.append(a)

    consumer['adminroles'] = adminroles

    return jsonify(
        {
            'result': True,
            'admin': consumer,
            'token': token.decode('UTF-8')
        }
    )




############################### Department Routes #############################

# List departments
@app.route('/departments', methods=['GET'])
@tokenOptional
def listDepartments(token):
    departments = api.list_departments()
    if token:
        return jsonify(list(map(to_dict, departments)))

    return jsonify(convertMinimal(departments, ['name', 'id']))


# Get department statistics
@app.route('/department/<int:id>/statistics', methods=['GET'])
@tokenRequired
def getDepartmentStatistics(id):
    return jsonify(api.getDepartmentStatistics(id))




############################### Consumer Routes ###############################

# List consumers
@app.route('/consumers', methods=['GET'])
@tokenOptional
def listConsumers(token):
    consumers = api.list_consumers()

    if token:
        consumers = list(map(to_dict, consumers))
        for consumer in consumers:
            del consumer['password']
        return jsonify(consumers)

    return jsonify(convertMinimal(consumers, ['name', 'id', 'active']))


# Insert consumer
@app.route('/consumers', methods=['POST'])
@tokenRequired
def insertConsumer():
    c = Consumer(**json_body())
    api.insert_consumer(c)
    return jsonify(result='created'), 201


# Get consumer
@app.route('/consumer/<int:id>', methods=['GET'])
def getConsumer(id):
    consumer = to_dict(api.get_consumer(id))
    if 'password' in consumer:
        del consumer['password']

    return jsonify(to_dict(api.get_consumer(id)))


# Update consumer
@app.route('/consumer/<int:id>', methods=['PUT'])
@tokenRequired
def updateConsumer(id):
    data = json_body()
    if 'credit' in data:
        del data['credit']
    if 'password' in data:
        data['password'] = bcrypt.generate_password_hash(data['password'])
    c = Consumer(**json_body())
    c.id = id
    api.update_consumer(c)
    return jsonify(result='updated'), 200  # TODO: another status code?


# Get consumer's favorite products
@app.route('/consumer/<int:id>/favorites', methods=['GET'])
def getConsumerFavorites(id):
    return jsonify(list(map(to_dict, api.get_favorite_products(id))))


# Get consumer's purchases
@app.route('/consumer/<int:id>/purchases', methods=['GET'])
def getConsumerPurchases(id):
    return jsonify(list(map(to_dict, api.get_purchases_of_consumer(id))))


# Get consumer's deposits
@app.route('/consumer/<int:id>/deposits', methods=['GET'])
def getConsumerDeposits(id):
    return jsonify(list(map(to_dict, api.get_deposits_of_consumer(id))))




############################### Product Routes ################################

# List products
@app.route('/products', methods=['GET'])
def listProducts():
    return jsonify(list(map(to_dict, api.list_products())))


# Insert product
@app.route('/products', methods=['POST'])
@tokenRequired
def insertProduct():
    api.insert_product(Product(**json_body()))
    return jsonify(result='created'), 201


# Get product
@app.route('/product/<int:id>', methods=['GET'])
def getProduct(id):
    return jsonify(to_dict(api.get_product(id)))


# Update product
@app.route('/product/<int:id>', methods=['PUT'])
@tokenRequired
def updateProduct(id):
    p = Product(**json_body())
    p.id = id
    api.update_product(p)
    return jsonify(result='updated'), 200




############################### Purchase Routes ###############################

# List purchases with or without limit
@app.route('/purchases', methods=['GET'])
@app.route('/purchases/<int:limit>', methods=['GET'])
def listPurchases(limit=None):
    return jsonify(list(map(to_dict, api.list_purchases(limit=limit))))


# Insert purchase
@app.route('/purchases', methods=['POST'])
def insertPurchase():
    api.insert_purchase(Purchase(**json_body()))
    return jsonify(result='created'), 201


# Get purchase
@app.route('/purchase/<int:id>', methods=['GET'])
def getPurchase(id):
    return jsonify(to_dict(api.get_purchase(id)))


# Update purchase
@app.route('/purchases/<int:id>', methods=['PUT'])
def updatePurchase(id):
    p = Purchase(**json_body())
    p.id = id
    api.update_purchase(p)
    return jsonify(result='updated'), 200



############################### Deposit Routes ################################

# List deposits with or without limit
@app.route('/deposits', methods=['GET'])
@app.route('/deposits/<int:limit>', methods=['GET'])
def listDeposits(limit=None):
    return jsonify(list(map(to_dict, api.list_deposits(limit=limit))))


# Insert deposit
@app.route('/deposits', methods=['POST'])
@tokenRequired
def insertDeposit():
    api.insert_deposit(Deposit(**json_body()))
    return jsonify(result='created'), 201


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

############################### Payoff Routes #################################

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


# List payoffs
@app.route('/payoffs', methods=['GET'])
def list_payoffs():
    return jsonify(list(map(to_dict, api.list_payoffs())))


# Insert payoff
@app.route('/payoff', methods=['POST'])
@tokenRequired
def insertPayoff():
    api.insert_payoff(Payoff(**json_body()))
    return jsonify(result='created'), 201


if __name__ == "__main__":
    app.run(host=app.config['HOST'], port=app.config['PORT'])
