#!/usr/bin/env python3
import json
import pdb
import sqlite3
import datetime
import argparse

from flask import Flask, Request, g, jsonify, request, make_response
from flask_bcrypt import Bcrypt
import jwt
from functools import wraps
from flask_cors import CORS
from werkzeug.local import LocalProxy
import project.configuration as config

from project.backend.db_api import (CanOnlyBeRevokedOnce, DatabaseApi, DuplicateObject,
                            FieldIsNone, ForbiddenField, ForeignKeyNotExisting,
                            ObjectNotFound, ConsumerNeedsCredentials)
from project.backend.models import (Consumer, Deposit, Payoff, Product,
                            Purchase, Workactivity)
from project.backend.validation import (FieldBasedException, InputException,
                                MaximumValueExceeded, MaxLengthExceeded,
                                MinLengthUndershot, UnknownField, WrongType,
                                to_dict)

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)
api = None

def set_app(configuration):
    global api
    app.config.from_object(configuration)
    connection = sqlite3.connect(app.config['DATABASE_URI'],
                                 detect_types=sqlite3.PARSE_DECLTYPES,
                                 check_same_thread=False)
    api = DatabaseApi(connection, app.config)
    return app, api

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Webapi for shop.db')
    parser.add_argument('--mode', default='productive',
                        choices=['productive', 'debug'])

    args = parser.parse_args()


    if args.mode == 'productive':
        # app.config.from_object(config.BaseConfig)
        set_app(config.BaseConfig)
    elif args.mode == 'debug':
        # app.config.from_object(config.DevelopmentConfig)
        set_app(config.DevelopmentConfig)
    else:
        sys.exit('{}: invalid operating mode'.format(args.mode))


def get_api():
    DB_URI = app.config['DATABASE_URI']
    db = sqlite3.connect(DB_URI, detect_types=sqlite3.PARSE_DECLTYPES)
    api = DatabaseApi(db, app.config)
    return api


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


def adminRequired(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'token' in request.headers:
            token = request.headers['token']

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            admin = data['admin']
            admin = api.get_consumer(admin['id'])
            adminroles = api.getAdminroles(admin)

            if not adminroles:
                return jsonify({'message': 'You are not an administrator!'}), 401

            admin = to_dict(admin)
            adminroles = []
            for a in adminroles:
                adminroles.append(a.department_id)

            admin['adminroles'] = adminroles

        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(admin, *args, **kwargs)
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
    if app.config['DEBUG']:
        raise e
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
        if not bcrypt.check_password_hash(consumer['password'], password):
            return make_response('Could not verify', 401)
    except:
        return make_response('Could not verify', 401)

    # Check if the consumer has administrator rights
    adminroles = api.getAdminroles(api.get_consumer(consumer['id']))
    if not adminroles:
        _type = 'consumer'
    else:
        _type = 'admin'
        consumer['adminroles'] = list(map(to_dict, adminroles))
        for role in consumer['adminroles']:
            role['timestamp'] = str(role['timestamp'])

    del consumer['password']

    # Define token
    exp = datetime.datetime.now() + datetime.timedelta(minutes=30)

    token = jwt.encode({_type: consumer, 'exp': exp}, app.config['SECRET_KEY'])

    result = {}
    result['result'] = True
    result[_type] = consumer
    result['token'] = token.decode('UTF-8')

    return jsonify(result)



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
@adminRequired
def getDepartmentStatistics(admin, id):
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
            cons = Consumer(id=consumer['id'])
            adminroles = list(map(to_dict, api.getAdminroles(cons)))
            consumer['adminroles'] = adminroles

        return jsonify(consumers)

    return jsonify(convertMinimal(consumers, ['name', 'id', 'active',
                                              'isAdmin', 'hasCredentials']))


# Insert consumer
@app.route('/consumers', methods=['POST'])
@adminRequired
def insertConsumer(admin):
    c = Consumer(**json_body())
    api.insert_consumer(c)
    return jsonify(result='created'), 201


# Get consumer
@app.route('/consumer/<int:id>', methods=['GET'])
def getConsumer(id):
    consumer = to_dict(api.get_consumer(id))
    if 'password' in consumer:
        del consumer['password']

    return jsonify(consumer)


# Update consumer
@app.route('/consumer/<int:id>', methods=['PUT'])
@adminRequired
def updateConsumer(admin, id):
    data = json_body()
    messages = []

    consumer = Consumer(id=id)
    _consumer = api.get_consumer(id=id)

    if 'credit' in data:
        del data['credit']

    if 'adminroles' in data:
        if data['adminroles']:
            # check if there are already consumer credentials in the database
            if any(v is None for v in [_consumer.email, _consumer.password]):
                # if not, check if credentials are in request data
                if any(v not in data for v in ['email', 'password']):
                    # if not, return failure
                    messages.append('Email and Password required to set adminroles!')
                    return jsonify(result=False, messages=messages), 200

            else:
                adminroles = data['adminroles']
        else:
            adminroles = False

        del data['adminroles']

    else:
        adminroles = False

    if 'password' in data:
        if 'repeatpassword' in data:
            if data['password'] == data['repeatpassword']:
                data['password'] = bcrypt.generate_password_hash(data['password'])
                del data['repeatpassword']
            else:
                message = {
                    'message': 'Passwords do not match!',
                    'error': True
                }
                messages.append(message)
                return jsonify(result=False, messages=messages), 200
        else:
            message = {
                'message': 'Please confirm your password!',
                'error': True
            }
            messages.append(message)
            return jsonify(result=False, messages=messages), 200


    for key, value in data.items():
        setattr(consumer, key, value)

    try:
        api.update_consumer(consumer)
        for key in data:
            message = {
                'message': 'Updated: {}'.format(key),
                'error': False
            }
            messages.append(message)
    except:
        message = {
            'message': 'Error updating consumer!',
            'error': True
        }
        messages.append(message)
        return jsonify(result=False, messages=messages), 200

    if adminroles:
        departments = api.list_departments()
        _apiAdminroles = api.getAdminroles(_consumer)

        for dep_id in adminroles.keys():
            department = api.get_department(id=int(dep_id))
            try:
                api.setAdmin(_consumer, department, adminroles[dep_id])
                message = {
                    'message': 'Adminrole set: {}'.format(department.name),
                    'error': False
                }

                messages.append(message)

            except ConsumerNeedsCredentials:
                message = {
                    'message': 'Consumer needs credentials in order to be admin!',
                    'error': True
                }
                messages.append(message)
                _consumer = to_dict(_consumer)
                rebaseConsumer = Consumer(**_consumer)
                api.update_consumer(rebaseConsumer)

                adminroles = [d.department_id for d in _apiAdminroles]

                for department in departments:
                    isAdmin = department.id in adminroles
                    api.setAdmin(rebaseConsumer, department, isAdmin)

                return jsonify(result=False, messages=messages), 200

    return jsonify(result=True, messages=messages), 200


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
@adminRequired
def insertProduct(admin):
    api.insert_product(Product(**json_body()))
    return jsonify(result='created'), 201


# Get product
@app.route('/product/<int:id>', methods=['GET'])
def getProduct(id):
    return jsonify(to_dict(api.get_product(id)))


# Update product
@app.route('/product/<int:id>', methods=['PUT'])
@adminRequired
def updateProduct(admin, id):
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
@adminRequired
def insertDeposit(admin):
    api.insert_deposit(Deposit(**json_body()))
    return jsonify(result='created'), 201




############################### Payoff Routes #################################

# List payoffs
@app.route('/payoffs', methods=['GET'])
def list_payoffs():
    return jsonify(list(map(to_dict, api.list_payoffs())))


# Insert payoff
@app.route('/payoff', methods=['POST'])
@adminRequired
def insertPayoff(admin):
    api.insert_payoff(Payoff(**json_body()))
    return jsonify(result='created'), 201



############################### Workactivity Routes ###########################

# List workactivities
@app.route('/workactivities', methods=['GET'])
def listWorkactivities():
    return jsonify(list(map(to_dict, api.list_workactivities())))


# Insert workactivity
@app.route('/workactivities', methods=['POST'])
@adminRequired
def insertWorkactivity(admin):
    api.insert_workactivity(Workactivity(**json_body()))
    return jsonify(result='created'), 201


# Get workactivity
@app.route('/workactivity/<int:id>', methods=['GET'])
def getWorkactivity(id):
    return jsonify(to_dict(api.get_workactivity(id)))


# Update workactivity
@app.route('/workactivity/<int:id>', methods=['PUT'])
@adminRequired
def updateWorkactivity(admin, id):
    data = json_body()
    workactivity = Workactivity(**json_body())
    workactivity.id = id
    messages = []
    try:
        api.update_workactivity(workactivity)
    except:
        message = {
            'message': 'Error while updating workactivity!',
            'error': True
        }
        messages.append(message)
        return jsonify(result=False, messages=messages), 200

    for key in data:
        message = {
            'message': 'Updated: {}'.format(key),
            'error': False
        }
        messages.append(message)

    return jsonify(result=True, messages=messages), 200




############################### Activity Routes ###############################

# List activities
@app.route('/activities', methods=['GET'])
@tokenOptional
def listActivities(token):
    activities = list(map(to_dict, api.list_activities()))
    if token:
        consumers = api.list_consumers()

        for activity in activities:
            activity['feedback'] = api.get_activityfeedback(activity_id=activity['id'])

    return jsonify(activities)


# Insert activity
@app.route('/activities', methods=['POST'])
@adminRequired
def insertActivity(admin):
    activity = Activity(**json_body())
    activity.created_by = admin.id
    api.insert_activity(activity)
    return jsonify(result='created'), 201


# Get activity
@app.route('/activity/<int:id>', methods=['GET'])
def getActivity(id):
    return jsonify(to_dict(api.get_activity(id)))


# Update activity
@app.route('/activity/<int:id>', methods=['PUT'])
@adminRequired
def updateActivity(admin, id):
    activity = Activity(**json_body())
    activity.id = id
    api.update_activity(p)
    return jsonify(result='updated'), 200



############################### Activityfeedback Routes #######################

# Get activityfeedback
@app.route('/activityfeedback/<int:id>', methods=['GET'])
@adminRequired
def getActivityfeedback(admin, id):
    activityfeedback = list(map(to_dict, api.get_activityfeedback(id=id)))
    return jsonify(activityfeedback)


# Insert activityfeedback
@app.route('/activityfeedback', methods=['POST'])
def insertActivityfeedback():
    api.insert_activityfeedback(Activityfeedback(**json_body()))
    return jsonify(result='created'), 201


if __name__ == '__main__':
    app.run(host=app.config['HOST'], port=app.config['PORT'])
