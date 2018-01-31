#!/usr/bin/env python3

import getpass
from backend.models import Consumer
from cli.utils import choice

consumerFields = {'name': {'mandatory': True, 'hidden': False},
                  'email': {'mandatory': False, 'hidden': False},
                  'password': {'mandatory': False, 'hidden': True},
                  'studentnumber': {'mandatory': False, 'hidden': False}
                  }

def add_consumer():
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
        consumer.email = input('email:')

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
            print('{:10s} *********'.format(key))
        else:
            print('{:10s} {}'.format(key, getattr(consumer, key)))

    correct = choice('Correct?', default=True)
    if correct is None or correct is False:
        sys.exit('Data was not correct. Exiting.')

    return consumer
