#!/usr/bin/python3
import argparse
import json
import os.path
import pdb
import sys

import requests

server = "http://10.12.42.9:5000"
consumer = None
# product id for coffee
product_id = 18


def get_consumer(_name):
    response = requests.get("{}/consumers".format(server))
    data = response.json()
    for i in data:
        if i['name'] == _name:
            return i


def send_request(_id, _amount):
    comment = 'purchase inserted via insert_purchase script'
    data = {"amount": _amount, "consumer_id": _id,
            "product_id": product_id, "comment": comment}
    params = json.dumps(data).encode('utf8')
    req = requests.post("{}/purchases".format(server), data=params,
                        headers={'content-type': 'application/json'})
    if req.json()['result'] != "created":
        print("Something went wrong:")
        print(req.json()['result'])
    else:
        print("Success")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Insert deposits to shop.db')
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
                    entity = entity.strip().split(' ')
                    amount = ''.join(entity[-1:])
                    name = ' '.join(entity[:-1])

                    consumer = get_consumer(_name=name)
                    if consumer is not None:
                        if int(amount) != 0:
                            print("sending request")
                            send_request(_id=consumer['id'],
                                         _amount=int(amount))
                            consumer = None
                            amount = None

                    else:
                        print("The consumer with the name {} \
                               does not exist".format(name))
        except OSError as err:
            sys.exit("Could not parse file: {}".format(err))

    else:
        parser.print_help()
