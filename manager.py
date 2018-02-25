#!/usr/bin/env python3

from project.webapi import *
import project.configuration as config
from flask_bcrypt import Bcrypt
from werkzeug.local import LocalProxy
from project.backend.models import Consumer
from project.cli.consumer import add_consumer, add_admin, remove_admin
from project.cli.department import add_department
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
               '\tadmin      Manage consumer admin roles\n'

    def add(self):
        parser = argparse.ArgumentParser(
            description='Adds an element to the database')

        parser.add_argument('type', choices=['consumer', 'department'])
        args = parser.parse_args(sys.argv[2:])

        if args.type == 'consumer':
            add_consumer(api, bcrypt)
        elif args.type == 'department':
            add_department(api)
        else:
            sys.exit('Invalid type: {}'.format(args.type))

    def admin(self):
        parser = argparse.ArgumentParser(
            description='Manage consumer admin roles')

        parser.add_argument('operation', choices=['add', 'remove'])
        args = parser.parse_args(sys.argv[2:])

        if args.operation == 'add':
            add_admin(api, bcrypt)
        elif args.operation == 'remove':
            remove_admin(api)
        else:
            sys.exit('{} is not a valid operation'.format(args.operation))


if __name__ == '__main__':
    app, api = set_app(config.BaseConfig)
    BackendManager()
