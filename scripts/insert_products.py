#!/usr/bin/python3
import argparse
import json
import os.path
import pdb
import sys

import requests

# server = "http://10.12.42.9:5000"
server = "http://0.0.0.0:5000"


def insert_product(name, price, department, revocable, active, on_stock):
    data = {"name": name, "price": price,
            "department_id": department, "active": active,
            "revocable": revocable,  "countable": True}
    params = json.dumps(data).encode('utf8')
    req = requests.post("{}/products".format(server), data=params,
                        headers={'content-type': 'application/json'})
    if req.json()['result'] != "created":
        print("Something went wrong:")
        print(req.json()['result'])
    else:
        print("Success")


def get_department(_name):
    response = requests.get("{}/departments".format(server))
    data = response.json()
    for i in data:
        if i['name'] == _name:
            return int(i['id'])


def parse_line(line):
    line = line.strip()
    line = line.split(" ")
    if len(line) == 6:
        try:
            product_name = str(line[0])
            price = int(line[1])
            department_name = str(line[2])
            revocable = True if int(line[3]) == 1 else False
            active = True if int(line[4]) == 1 else False
            on_stock = True if int(line[5]) == 1 else False
        except:
            print("cannot parse {}".format(line))
            return None

    elif len(line) > 6:
        try:
            product_name = str(" ".join(line[0:-5]))
            price = int(line[-5])
            department_name = str(line[-4])
            revocable = True if int(line[-3]) == 1 else False
            active = True if int(line[-2]) == 1 else False
            on_stock = True if int(line[-1]) == 1 else False
            answer = None

            # while answer not in ["yes", "no", "y", "n", ""]:
            #     answer = input(
            #         "Is the product name {} correct? (Yes/no): ".format(product_name))
            #
            # if answer in ["no", "n"]:
            #     product_name = input("Please enter the correct name: ")
        except:
            print("cannot parse {}".format(line))
            return None
    else:
        print("cannot parse {}".format(line))
        return None

    return [product_name, price, department_name, revocable, active, on_stock]


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
                        name = data[0]
                        price = data[1]
                        department = data[2]
                        revocable = data[3]
                        active = data[4]
                        on_stock = data[5]

                        department = get_department(_name=department)
                        if department is not None:
                            insert_product(name=name, price=price,
                                           department=department,
                                           revocable=revocable,
                                           active=active,
                                           on_stock=on_stock)
                        else:
                            print("The department with the name {} \
                                   does not exist".format(department))
        except OSError as err:
            sys.exit("Could not parse file: {}".format(err))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
