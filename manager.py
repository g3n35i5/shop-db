#!/usr/bin/env python3

from webapi import app, get_api
import configuration as config
from flask_bcrypt import Bcrypt
from werkzeug.local import LocalProxy
from backend.models import Consumer
from cli.consumer import add_consumer
import argparse
import sys

class BackendManager:
    def __init__(self):
        parser = argparse.ArgumentParser(description='Management interface '
                                         ' for the shop.db backend',
                                         usage=self.help_message())

        parser.add_argument('command', help='Command to run')
        args = parser.parse_args(sys.argv[1:2])

        if not hasattr(self, args.command):
            parser.print_help()
            exit(1)
        getattr(self, args.command)()

    def help_message(self):
        return 'manager <command> [<args>]\n' \
               '\tThe most commonly used commands are:\n' \
               '\tadd        Adds an element to the database\n' \
               '\tupdate     Updates an element of the database\n' \
               '\tmakeAdmin  Set a consumer as administrator\n'

    def add(self):
        parser = argparse.ArgumentParser(
            description='Adds an element to the database')

        parser.add_argument('type', choices=['consumer'])
        args = parser.parse_args(sys.argv[2:])

        if args.type == 'consumer':
            consumer = add_consumer()
            try:
                api.insert_consumer(consumer)
                print("Success")
            except:
                print("Error")


if __name__ == '__main__':
    bcrypt = Bcrypt(app)
    app.config.from_object(config.BaseConfig)
    api = LocalProxy(get_api)
    BackendManager()
