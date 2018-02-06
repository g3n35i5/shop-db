#!/usr/bin/python3

import argparse
import json
import os.path
import pdb
import sys

import requests


default_address = 'http://0.0.0.0'
default_port = '5000'
valid_elements = ['consumer', 'product', 'deposit', 'payoff', 'purchase']

'''
These dictionaries define all mandatory elements you need to insert the
specific element. The key is the human readable text displayed in the console,
the value is the corresponding variable name sent to the backend.
'''

mandatory_product = {'name': 'name',
                     'price': 'price',
                     'department name': 'department_id'}

mandatory_consumer = {'name': 'name'}
optional_consumer = {'active': 'active',
                     'credit': 'credit',
                     'karma': 'karma'}

mandatory_deposit = {'consumer name': 'consumer_id',
                     'amount': 'amount',
                     'comment': 'comment'}


class Consumer():

    def __init__(self, name, active=True, credit=0, karma=0):
        self.name = name
        self.active = active
        self.credit = credit
        self.karma = karma

    def get_name(self):
        return self.name

    def get_active(self):
        return self.active

    def get_credit(self):
        return self.credit

    def get_karma(self):
        return self.karma


def index_of_number_in_list(_list):
    ind = -1
    if not _list:
        return None

    for index in range(0, len(_list)):
        try:
            number = int(_list[index])
            ind = index
            break
        except Exception as e:
            pass
    return ind if ind is not -1 else None


def print_http_result(result, data):
    if result.json()['result'] != "created":
        print("Cant insert {}".format(data))
    else:
        print("Success")


def insert_consumers(consumers):
    for consumer in consumers:
        name = consumer.get_name()
        active = consumer.get_active()
        karma = consumer.get_karma()
        credit = consumer.get_credit()
        data = {"name": name, "credit": credit,
                "active": active, "karma": karma}
        params = json.dumps(data).encode('utf8')
        req = requests.post("{}/consumers".format(server), data=params,
                            headers={'content-type': 'application/json'})

        print_http_result(req, data)


def get_consumers():
    response = requests.get("{}/consumers".format(server))
    return response.json()


def read_file_to_list(filename):
    relevant_lines = []
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line:
                    if line[0] is not '#' and line[0] is not '':
                        relevant_lines.append(line)
        if len(relevant_lines) > 1:
            return relevant_lines
        else:
            sys.exit('There are no valid lines in file {}'.format(filename))
    except Exception as e:
        sys.exit('Error while reading file {}, error: {}'.format(filename, e))


def get_data(data, _type):
    print('Please enter the {} values'.format(_type))
    cont = None
    mandatory = []
    while cont not in ['yes', 'y', '']:
        for key in data:
            answer = input('{} > '.format(key))
            mandatory.append(answer)

        print('Please check if the following values are correct:')
        i = 0
        for key in data:
            print('{}: {}'.format(key, mandatory[i]))
            i += 1

        cont = input('Are the values correct? (Yes/no) > ')
    return mandatory


def single_consumer():
    '''
    This function will guide the user in oder to insert a single consumer
    '''
    mandatory = mandatory_consumer
    optional = optional_consumer

    man_data = get_data(mandatory, 'mandatory')
    need_optional = None
    while need_optional not in ['yes', 'no', 'y', 'n', '']:
        need_optional = input(
            'Do you want to change other values? (yes/No) > ')
    opt_data = None
    if need_optional in ['yes', 'y']:
        opt_data = get_data(optional, 'optional')
    name = man_data[0]
    if opt_data is not None:
        try:
            active = int(opt_data[0])
            credit = int(opt_data[1])
            karma = int(opt_data[2])
        except Exception as e:
            sys.exit(
                'Optional consumer data is corrupt: {}, error: {}'.format(opt_data, e))
    else:
        active = True
        credit = 0
        karma = 0
    c = Consumer(name=name, credit=credit, active=active, karma=karma)
    insert_consumers([c])


def handle_insert_consumer(line_list):
    '''
    This function handles a list of lines parsed out of the specified file
    '''
    consumers = []
    for line in line_list:
        '''
        Set all default values and name to empty string
        '''

        name = ''
        credit = 0
        karma = 0
        active = True
        line = line.split(' ')
        line = [i for i in line if i != '']
        ind = index_of_number_in_list(line)
        if ind is None:
            '''
            This is the first possible case, there is only a name in this line
            '''
            consumers.append(Consumer(name=' '.join(line)))
            continue
        else:
            '''
            This is the second big case, the is a name and one or more
            parameters to create this consumer
            '''
            name = ' '.join(line[0: ind])
            remain = line[ind:]
            line = [name]
            for i in remain:
                line.append(i)

            # Case 1: Name and credit
            if len(line) == 2:
                credit = int(line[1])
                consumers.append(Consumer(name=name, credit=credit))
                continue

            # Case 2: Name, credit and active
            elif len(line) == 3:
                credit = int(line[1])
                active = True if int(line[2]) == 1 else False
                consumers.append(Consumer(name=name, credit=credit,
                                          active=active))
                continue

            # Case 3: Name, credit, active and karma
            elif len(line) == 4:
                credit = int(line[1])
                active = True if int(line[2]) == 1 else False
                karma = int(line[3])
                consumers.append(Consumer(name=name, credit=credit,
                                          active=active, karma=karma))
                continue
            else:
                sys.exit('Error while parsing consumer insert list, {}\
                          is not a valid line'.format(line))
    insert_consumers(consumers)


def main():
    parser = argparse.ArgumentParser(description='Insert elements to shop.db')
    parser.add_argument('-t', '--type',
                        help='Specify the element you want to insert',
                        choices=valid_elements,
                        default=None)
    parser.add_argument('-f', '--file',
                        help='text file with data you want to insert',
                        default=None)
    parser.add_argument('-s', '--server',
                        help='The url resp. ip address of the server',
                        default=default_address)
    parser.add_argument('-p', '--port',
                        help='The port the api is served on',
                        default=default_port)

    args = vars(parser.parse_args())
    global server
    server = ':'.join([args['server'], args['port']])

    if args['type'] not in valid_elements:
        sys.exit('You need to specify the type of element you want to insert')
    if args['file'] is not None:
        lines = read_file_to_list(args['file'])
        ele_type = lines[0].split('=')
        if ele_type[0] != 'TYPE' or ele_type[1] not in valid_elements:
            sys.exit('{} has not a valid format or element type {} does \
            not match with the specified type {}'.format(
                args['file'], ele_type[1], args['type']))
        else:
            del lines[0]
            if args['type'] == 'consumer':
                handle_insert_consumer(lines)
            else:
                sys.exit(
                    'Inserting {} is not implemented yet'.format(args['type']))
    else:
        if args['type'] == 'consumer':
            single_consumer()


if __name__ == "__main__":
    main()
