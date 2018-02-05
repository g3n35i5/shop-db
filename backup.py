#!/usr/bin/env python3

import datetime
import os
import sqlite3
import sys
from configuration import BaseConfig

if __name__ == '__main__':
    _currentDate = datetime.datetime.now()
    _filepath = BaseConfig.BACKUP_DIR + _currentDate.strftime('%Y/%B/%d/')
    _filename = _currentDate.strftime('%H_%M_%S') + '.dump'
    dumpfile =  _filepath + _filename

    if not os.path.exists(_filepath):
        try:
            os.makedirs(os.path.dirname(_filepath))

        except OSError as exc:
            if exc.errno != errno.EEXIST:
                sys.exit("Error while creating directory.")
                raise

    try:
        con = sqlite3.connect(BaseConfig.DATABASE_URI)
    except:
        sys.exit('Could not open shop-db database')

    try:
        f = open(dumpfile, 'w+')

        for line in con.iterdump():
            f.write('{}\n'.format(line))

        f.close()
    except:
        sys.exit('Could not write backup to file "{}"'.format(dumpfile))

    con.close()
