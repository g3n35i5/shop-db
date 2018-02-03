#!/usr/bin/env python3

import getpass
from backend.models import Consumer
from cli.utils import choice, find
import sys
import pdb

consumerFields = {'name': {'mandatory': True, 'hidden': False},
                  'email': {'mandatory': False, 'hidden': False},
                  'password': {'mandatory': False, 'hidden': True},
                  'studentnumber': {'mandatory': False, 'hidden': False}
                  }


def _get_password(bcrypt):
    password = None
    rep_password = None

    while not password or password != rep_password:
        password = getpass.getpass()
        rep_password = getpass.getpass(prompt='Repeat password:')

        if password != rep_password:
            password = None
            rep_password = None
            print('Passwords do not match! Please try again.\n')

    return bcrypt.generate_password_hash(password)

def _get_consumer(api, name):
    consumers = api.list_consumers()
    for consumer in consumers:
        if consumer.name == name:
            return consumer

    sys.exit('There is no consumer with the name "{}"'.format(name))

def _enter_login_data(consumer, api, bcrypt):
    print('')
    print('The consumer has not stored any login data.')
    print('These must be entered first so that he/she can become')
    print('an administrator.')
    print('')

    upConsumer = Consumer(id=consumer.id)

    if consumer.email is None:
        upConsumer.email = input('email: ')

    if consumer.password is None:
        upConsumer.password = _get_password(bcrypt)

    print('')

    try:
        api.update_consumer(upConsumer)
    except:
        sys.exit('The login data could not be updated.')

    print('The login data have been successfully updated')

def add_admin(api, bcrypt):
    print('Promote a user to the admin for one or more departments\n')
    consumer = _get_consumer(name=input('consumer name: '), api=api)
    if not all([consumer.password, consumer.email]):
        _enter_login_data(consumer, api, bcrypt)

    _departments = api.list_departments()
    _adminroles = api.getAdminroles(consumer)

    print('')
    for dep in _departments:
        if dep.id not in [x.department_id for x in _adminroles]:
            if choice('Make admin for department {}?'.format(dep.name)):
                try:
                    api.setAdmin(consumer=consumer, department=dep, admin=True)
                except:
                    sys.exit('Could not set consumer as admin.')
        else:
            print('{:20s} Already admin'.format(dep.name + ':'))

def remove_admin(api):
    print('Revoke consumer administrator rights to one or more departments\n')
    consumer = _get_consumer(name=input('consumer name: '), api=api)
    _adminroles = api.getAdminroles(consumer)
    _departments = api.list_departments()

    if not _adminroles:
        sys.exit('The consumer "{}" is not an administrator ' \
                 'for any department yet'.format(consumer.name))

    for role in _adminroles:
        dep = find(lambda dep: dep.id == role.department_id, _departments)
        if choice('Revoke rights for department {}?'.format(dep.name)):
            try:
                api.setAdmin(consumer=consumer, department=dep, admin=False)
            except:
                sys.exit('The adminrole for the department {} ' \
                         'could not be revoked.'.format(dep.name))


def add_consumer(api, bcrypt):
    print('Please enter the data of the new consumer:')

    # Get name
    name = input('name: ')

    # Create new consumer object
    consumer = Consumer(name=name)

    # Choice of whether to enter additional information
    extra = None
    while extra is None:
        extra = choice('Should the user be able to log in?')

    if extra:
        # Get email adress
        consumer.email = input('email: ')

        # Get password
        password = None
        rep_password = None

        while not password or password != rep_password:
            password = getpass.getpass()
            rep_password = getpass.getpass(prompt='Repeat password:')

            if password != rep_password:
                password = None
                rep_password = None
                print('Passwords do not match! Please try again.\n')

        consumer.password = bcrypt.generate_password_hash(password)

        try:
            studentnumber = input('Studentnumber: ')
            consumer.studentnumber = int(studentnumber)
        except ValueError:
            sys.exit('Could not convert "{}" to int'.format(studentnumber))


    print('Please check if the following data is correct\n')

    for key in consumer.__dict__['_data']:
        if consumerFields[key]['hidden']:
            print('{:20s} *********'.format(key + ':'))
        else:
            print('{:20s} {}'.format(key + ':', getattr(consumer, key)))

    print('')
    correct = choice('Correct?', default=True)
    if correct is None or correct is False:
        sys.exit('Data was not correct. Exiting.')

    try:
        api.insert_consumer(consumer)
        print("success")
    except:
        sys.exit("error")
