#!/usr/bin/python3
import argparse
import json
import os.path
import pdb
import sys

import requests

server = "http:/shop.gatrobe.de:5000"


def insert_payoff(department_id, amount):
    data = {"department_id": department_id, "amount": amount}
    params = json.dumps(data).encode('utf8')
    r = requests.post("{}/payoff".format(server), data=params,
                      headers={'content-type': 'application/json'})

    if r.json()['result'] != "created":
        print("Something went wrong:")
        print(r.json()['result'])
    else:
        print("Success")


def get_department(_name):
    with requests.urlopen("{}/departments".format(server)) as response:
        data = json.loads(response.read())
        for i in data:
            if i['name'] == _name:
                return int(i['id'])


def parse_line(line):
    line = line.strip()
    line = line.split(" ")
    if len(line) == 2:
        try:
            department_name = str(line[0])
            amount = int(line[1])
        except:
            print("cannot parse {}".format(line))
            return None

    else:
        print("cannot parse {}".format(line))
        return None

    return [department_name, amount]


def main():
    # format for each line:
    # product_name price_in_cents department_name revocable active on_stock
    parser = argparse.ArgumentParser(description='Insert products to shop.db')
    parser.add_argument('-f', '--file',
                        help='text file with names, products and amounts',
                        default=None)
    args = vars(parser.parse_args())

    if args['file'] is not None:
        if not os.path.exists(args['file']):
            sys.exit("{} does not exists".format(args['file']))

        try:
            with open(args['file']) as _file:
                data = _file.readlines()
                for entity in data:
                    data = parse_line(entity)
                    if data is not None:
                        department_name = data[0]
                        amount = data[1]

                        department = get_department(_name=department_name)
                        if department is not None:
                            insert_payoff(
                                department_id=department, amount=amount)
                        else:
                            print("The department with the name {} \
                                   does not exist".format(department))
        except OSError as err:
            sys.exit("Could not parse file: {}".format(err))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
