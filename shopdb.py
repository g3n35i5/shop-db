#!/usr/bin/env python3

import argparse
import sys
from project.webapi import *
import project.configuration as config

parser = argparse.ArgumentParser(description='Webapi for shop.db')
parser.add_argument('--mode', default='productive',
                    choices=['productive', 'debug'])
args = parser.parse_args()

if args.mode == 'productive':
    set_app(config.BaseConfig)
elif args.mode == 'debug':
    set_app(config.DevelopmentConfig)
else:
    sys.exit('{}: invalid operating mode'.format(args.mode))

app.run(host=app.config['HOST'], port=app.config['PORT'])
