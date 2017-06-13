#!/usr/bin/python3
import argparse
import json
import os.path
import pdb
import sys

import requests

# server = "http://10.12.42.9:5000"
server = "http://0.0.0.0:5000"


def insert_consumer(name, credit, active, karma):

    data = {"name": name, "credit": credit, "active": active, "karma": karma}
    params = json.dumps(data).encode('utf8')
    req = requests.post("{}/consumers".format(server), data=params,
                        headers={'content-type': 'application/json'})
    response = urllib.request.urlopen(req)
    if req.json()['result'] != "created":
        print("Something went wrong:")
        print(req.json()['result'])
    else:
        print("Success")


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
                data = _file.read()
                data = json.loads(data)
                for item in data:
                    name = str(item['name'])
                    credit = int(item['credit'])
                    active = item['active']
                    if 'karma' in item:
                        karma = item['karma']
                    else:
                        karma = -10
                    insert_consumer(name, credit, active, karma)

        except OSError as err:
            sys.exit("Could not parse file: {}".format(err))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
