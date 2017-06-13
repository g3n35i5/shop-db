#!/usr/bin/python3
import argparse
import json
import os.path
import pdb
import sys
import urllib.request

server = "http://0.0.0.0:5000"
consumer = None


def index_of_number_in_list(_list):
    for index in range(0, len(_list)):
        try:
            number = int(_list[index])
            return index
        except ValueError:
            pass


def get_consumer(_name):
    try:
        with urllib.request.urlopen("{}/consumers".format(server)) as response:
            data = json.loads(response.read())
            for i in data:
                if i['name'] == _name:
                    return i
    except:
        pass


def send_request(_id, _amount, _comment):
    data = {"consumer_id": _id, "amount": _amount, "comment": _comment}
    params = json.dumps(data).encode('utf8')
    req = urllib.request.Request("{}/deposits".format(server), data=params,
                                 headers={'content-type': 'application/json'})
    response = urllib.request.urlopen(req)
    if response.msg != "CREATED":
        print("Something went wrong:")
        print(response.msg)
    else:
        print("Success")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Insert deposits to shop.db')
    parser.add_argument('-n', '--name',
                        help='consumer name',
                        default=None)
    parser.add_argument('-a', '--amount',
                        help='deposit amount in cents',
                        default=None)
    parser.add_argument('-c', '--comment',
                        help='deposit comment',
                        default=None)
    parser.add_argument('-f', '--file',
                        help='text file with names and amounts',
                        default=None)
    args = vars(parser.parse_args())

    if args['file'] is not None:
        if args['name'] is None and args['amount'] is None and args['comment'] is None:
            if not os.path.exists(args['file']):
                sys.exit("{} does not exists".format(args['file']))

        else:
            sys.exit("If you specify a file, the -n, -a and -c options are invalid")

        try:
            with open(args['file']) as _file:
                data = _file.readlines()
                for entity in data:
                    entity = entity.strip().split(' ')
                    try:
                        amount_ind = index_of_number_in_list(entity)
                        amount = int(entity[amount_ind])
                        name = ' '.join(entity[0: amount_ind])
                        comment = ' '.join(entity[amount_ind + 1:])

                        try:
                            consumer = get_consumer(_name=name)
                            if consumer is not None:
                                print("sending request")
                                send_request(_id=consumer['id'],
                                             _amount=amount,
                                             _comment=comment)
                                consumer = None

                            else:
                                print("The consumer with the name {} \
                                       does not exist".format(name))
                        except:
                            print('error while fetching consumer, skipping')
                    except:
                        print('error while fetching line, skipping')

        except:
            sys.exit("Could not parse file")

    elif args['name'] is not None and args['amount'] is not None and args['comment'] is not None:
        if args['file'] is None:
            consumer = get_consumer(args['name'])
            amount = int(args['amount'])
            comment = args['comment']
            if consumer is not None:
                send_request(_id=consumer['id'],
                             _amount=amount, _comment=comment)
        else:
            sys.exit("If you specify the name and an amount the - f \
                     option is invalid")

    else:
        parser.print_help()
