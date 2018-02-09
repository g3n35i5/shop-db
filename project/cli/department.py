#!/usr/bin/env python3

from project.backend.models import Department
from project.cli.utils import choice
import sys

departmentFields = {'name': {'mandatory': True, 'hidden': False},
                    'budget': {'mandatory': True, 'hidden': False}
                    }

def add_department(api):
    print('Add a department to shop-db\n')

    try:
        name = str(input('Department name: '))
    except:
        sys.exit('Invalid name')

    try:
        budget = int(input('Department budget in cents: '))
    except:
        sys.exit('Invalid budget')

    department = Department(name=name, budget=budget)

    print('Please check if the following data is correct\n')

    for key in department.__dict__['_data']:
        if departmentFields[key]['hidden']:
            print('{:20s} *********'.format(key + ':'))
        else:
            print('{:20s} {}'.format(key + ':', getattr(department, key)))

    print('')

    correct = choice('Correct?', default=True)
    if correct is None or correct is False:
        sys.exit('Data was not correct. Exiting.')

    try:
        api.insert_department(department)
    except:
        sys.exit('Could not add department')
