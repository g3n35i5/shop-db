#!/usr/bin/env python3

import os
import sys
import sqlite3
from shutil import copyfile
from project.configuration import BaseConfig
from project.cli.utils import choice

print('WARNING')
print('')
print('This script deletes all payoffs following the '
      '"\schema <amount>x <productname>" in the name.')
confirm = choice('Are you sure you want to do this?')
if not confirm:
    sys.exit('Exit')

# Do a backup of the database
copyfile(BaseConfig.DATABASE_URI, BaseConfig.DATABASE_URI + '.backup')

# Connect to the database
conn = sqlite3.connect(BaseConfig.DATABASE_URI)
cur = conn.cursor()

# create text document with all deleted rows
f = open('deleted_rows_update_departmentpurchasecollections.txt', 'w')
# Get payoffs
cur.execute('SELECT * FROM payoffs WHERE departmentpurchase_id NOT NULL;')
payoffs = cur.fetchall()
for payoff in payoffs:
    amount = payoff[4]
    department_id = payoff[1]
    cur.execute('UPDATE departments SET expenses=expenses-? WHERE id=?;',
                (amount, department_id)
                )


with open('0_update.sql') as update:
    update = update.read()

conn.executescript(update)
