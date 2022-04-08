#!/usr/bin/env python3

''' slurm_sus.py -- Get SUs from slurm_bank.db
Usage:
    slurm_sus.py <account>
    slurm_sus.py -h | --help
    slurm_sus.py -v | --version

Positional Arguments:
    <account>       The Slurm account

Options:
    -h --help                       Print this screen and exit
    -v --version                    Print the version of slurm_sus.py
'''

import sys
import dataset
from docopt import docopt
from py_settings import DATABASE,DB_TABLE_NAME

# Test:
# 1. Make sure item exists
def check_item_in_table(table, account):
    if table.find_one(account=account) is None:
        sys.exit(f"ERROR: The {account}: {0} doesn't appear to exist")

# The magical mystical docopt line
arguments = docopt(__doc__, version='slurm_sus.py version 0.0.1')

# Connect to the database and get the limits table
# Absolute path ////
db = dataset.connect(f'sqlite:///{DATABASE}')

db_table = db[DB_TABLE_NAME]

# Check that account exists
check_item_in_table(db_table, arguments['<account>'])

# Print out SUs
SUSTRING = "Account {0} has {1} Service Units (SUs)"
ServiceUnits = db_table.find_one(account=arguments['<account>'])['su_limit_hrs']
print(SUSTRING.format(arguments['<account>'], ServiceUnits))
