#!/usr/bin/env python3

''' slurm_bank.py -- Deal with slurm_bank.db
Usage:
    slurm_bank.py insert <account> <su_limit_hrs>
    slurm_bank.py modify <account> <su_limit_hrs>
    slurm_bank.py add <account> <su_limit_hrs>
    slurm_bank.py get_sus <account>
    slurm_bank.py check_service_units_limit <account>
    slurm_bank.py check_end_of_date_limit <account>
    slurm_bank.py reset_usage <account>
    slurm_bank.py release_hold <account>
    slurm_bank.py three_month_check <account>
    slurm_bank.py dump <filename>
    slurm_bank.py repopulate <filename>
    slurm_bank.py -h | --help
    slurm_bank.py -v | --version

Positional Arguments:
    <account>       The Slurm account
    <su_limit_hrs>  The limit in CPU Hours (e.g. 10,000)
    <filename>      Dump to or repopulate from file, format is JSON

Options:
    -h --help                       Print this screen and exit
    -v --version                    Print the version of slurm_bank.py
'''

# Default is python 2.6, can't use subprocess
from os import popen
from os.path import exists, dirname, realpath
from datetime import date, datetime, timedelta
#import smtplib
#from email.mime.text import MIMEText
import json
import sys
from datafreeze import freeze
from docopt import docopt
import dataset
import py_sb_settings

# Test:
# 1. Is the number of service units really an integer?
# 2. Is the number of service units greater than the default?
def check_service_units(given_integer):
    try:
        service_units_check = int(given_integer)
        if service_units_check == -1:
            print("WARNING: Giving the group infinite SUs")
        elif service_units_check < py_sb_settings.DEFAULT_ALLOCATION:
            sys.exit(f"ERROR: Number of SUs => {service_units_check} is too small!\nEXPLANATION: Default (therefore min) allocation is: "+str(py_sb_settings.DEFAULT_ALLOCATION))
        return service_units_check
    except ValueError:
        sys.exit(f"ERROR: The given limit => {given_integer} is not an integer!")


# Test:
# 1. Does association for account and all clusters exists in Slurm database?
def check_account_and_cluster(account):
    for cluster in py_sb_settings.CLUSTERS:
        sacctmgr_command = "sacctmgr -n show assoc account={0} cluster={1} format=account,cluster"
        check_string = popen(sacctmgr_command.format(account, cluster)).read().split('\n')[0]
        if check_string.strip() == "":
            sys.exit(f"ERROR: no association for account {account} on cluster {cluster}")


# Test:
# 1. On insert, does item already exist in the database?
def check_insert_item_in_table(table, account):
    if not table.find_one(account=account) is None:
        sys.exit(f"ERROR: Account {account} already exists in database, did you want to modify it?")


# Test:
# 1. On modify, make sure item exists
def check_item_in_table(table, account, mode):
    if table.find_one(account=account) is None:
        if mode in ("modify", "check"):
            sys.exit(f"ERROR: Account {account} doesn't exists in database, did you want to insert it?")
        elif mode == 'reset_usage':
            sys.exit(f"ERROR: Account {account} doesn't exists in database, you should create a limit before resetting?")


# Logging function
def log_action(string):
    with open(py_sb_settings.LOGFILE, 'a+', encoding="utf8") as file_write:
        file_write.write(f"{datetime.now()}: {string}\n")

# The magical mystical docopt line, options_first=True because su_limit_hrs can be negative!
arguments = docopt(__doc__, version='slurm_bank.py version 0.0.1', options_first=True)

# Check account and cluster associations actually exist
# -> these won't exist for dump or repopulate
if not (arguments['dump'] or arguments['repopulate']):
    check_account_and_cluster(arguments['<account>'])

if not exists(dirname(realpath(py_sb_settings.DATABASE))):
    print(dirname(realpath(py_sb_settings.DATABASE)))
    sys.exit("ERROR: folder path to store Database doesn't exist!")

#Check if the DB file exists, if not create it
if not exists(py_sb_settings.DATABASE):
    open(py_sb_settings.DATABASE, 'a').close()

# Connect to the database and get the limits table
# Absolute path ////
db = dataset.connect(f'sqlite:///{py_sb_settings.DATABASE}')
# Global var
db_table = db[py_sb_settings.DB_TABLE_NAME]

# Insert a new project in the DB
# For each insert/update/check, do operations
if arguments['insert']:
    # Check if database item already exists
    check_insert_item_in_table(db_table, arguments['<account>'])

    # Check <su_limit_hrs>
    service_units = check_service_units(arguments['<su_limit_hrs>'])

    # Insert the limit
    db_table.insert(dict(account=arguments['<account>'], su_limit_hrs=service_units,
                 date=date.today(), upper_limit_informed=False, lower_limit_informed=False, max_limit_informed=False))

    # Log the action
    log_action(f"Account: {arguments['<account>']} Insert: {service_units}")

#Modify a project in the DB, to change SUs total
elif arguments['modify']:
    # Check if database item exists
    check_item_in_table(db_table, arguments['<account>'], 'modify')

    # Check <su_limit_hrs>
    service_units = check_service_units(arguments['<su_limit_hrs>'])

    # Modify the limit
    db_table.update(dict(account=arguments['<account>'], su_limit_hrs=service_units,
                 date=date.today(), upper_limit_informed=False, lower_limit_informed=False, max_limit_informed=False), ['account'])

    # Log the action
    log_action(f"Account: {arguments['<account>']} Modify: {service_units}")

#Modify a project in the DB, to add to SUs total
elif arguments['add']:
    # Check if database item exists
    check_item_in_table(db_table, arguments['<account>'], 'modify')

    # Check <su_limit_hrs>
    service_units = check_service_units(arguments['<su_limit_hrs>'])
    service_units += db_table.find_one(account=arguments['<account>'])['su_limit_hrs']

    # Modify the limit, but not the date
    db_table.update(dict(account=arguments['<account>'], su_limit_hrs=service_units,
                 upper_limit_informed=False, lower_limit_informed=False, max_limit_informed=False), ['account'])

    # Log the action
    log_action(f"Account: {arguments['<account>']} Add, New Limit: {service_units}")

elif arguments['check_service_units_limit']:
    # Check if database item exists
    check_item_in_table(db_table, arguments['<account>'], 'check')

    # Get the usage from `sshare` for the account on each cluster
    COMMAND = "sshare --noheader --account={0} --cluster={1} --format=RawUsage"
    RAWUSAGE = 0
    for cluster_sul in py_sb_settings.CLUSTERS:
        RAWUSAGE += int(popen(COMMAND.format(arguments['<account>'],
                               cluster_sul)).read().split('\n')[1].strip())

    # raw usage is in CPU Seconds
    RAWUSAGE /= (60 * 60)

    # Get limit in database
    limit = db_table.find_one(account=arguments['<account>'])['su_limit_hrs']

    # Check for 90% usage, send email
    if limit in (0, -1):
        PERCENT = 0
    else:
        PERCENT = 100 * int(RAWUSAGE) / limit

    # Check to see if account exceeds limit. If the limit is -1 the usage is unlimited.
    if limit != -1 and int(RAWUSAGE) > limit:
        # Account reached limit, set hold on account
        COMMAND = "sacctmgr -i modify account where account={0} cluster={1} set "+str(py_sb_settings.ACCOUNT_HOLD)+"=cpu=0"
        for cluster_sul2 in py_sb_settings.CLUSTERS:
            popen(COMMAND.format(arguments['<account>'], cluster_sul2))

        if limit != 0:
            informed = db_table.find_one(account=arguments['<account>'])['max_limit_informed']
            if not informed:

                # *******************INFORM ACTION REQUIRED********************

                # Log the action
                log_action(f"Account: {arguments['<account>']} Held")

                # PI has been informed
                db_table.update(dict(account=arguments['<account>'], max_limit_informed=True),
                            ['account'])

    # Check to see if account exceeds py_sb_settings.UPPER_LIMIT_PERCENT
    elif limit != -1 and PERCENT >= py_sb_settings.UPPER_LIMIT_PERCENT:
        informed = db_table.find_one(account=arguments['<account>'])['upper_limit_informed']
        if not informed:
            # Account is close to limit, inform PI

            # *******************INFORM ACTION REQUIRED********************

            # PI has been informed
            db_table.update(dict(account=arguments['<account>'], upper_limit_informed=True),
                        ['account'])

   # Check to see if account exceeds py_sb_settings.LOWER_LIMIT_PERCENT
    elif limit != -1 and PERCENT >= py_sb_settings.LOWER_LIMIT_PERCENT:
        informed = db_table.find_one(account=arguments['<account>'])['lower_limit_informed']
        if not informed:
            # Account is close to limit, inform PI

            # *******************INFORM ACTION REQUIRED********************

            # PI has been informed
            db_table.update(dict(account=arguments['<account>'], lower_limit_informed=True),
                        ['account'])

elif arguments['reset_usage']:
    # Check if database item exists
    check_item_in_table(db_table, arguments['<account>'], 'reset_usage')

    # Reset sshare usage
    COMMAND = "sacctmgr -i modify account where account={0} cluster={1} set RawUsage=0"
    for cluster_rs in py_sb_settings.CLUSTERS:
        popen(COMMAND.format(arguments['<account>'], cluster_rs))

    # Update the date in the database
    db_table.update(dict(account=arguments['<account>'], date=date.today(), upper_limit_informed=False, lower_limit_informed=False, max_limit_informed=False), ['account'])

    # Log the action
    log_action(f"Account: {arguments['<account>']} Reset")

elif arguments['check_end_of_date_limit']:
    # Check if database item exists
    check_item_in_table(db_table, arguments['<account>'], 'check')

    # Check date is (py_sb_settings.PROPOSAL_LENGTH_DAYS+1) or more days from previous
    db_date = db_table.find_one(account=arguments['<account>'])['date']
    current_date = date.today()
    comparison_days = current_date - db_date

    if comparison_days.days > py_sb_settings.PROPOSAL_LENGTH_DAYS:
        # If the usage was unlimited, just update the date otherwise set to py_sb_settings.DEFAULT_ALLOCATION
        limit = db_table.find_one(account=arguments['<account>'])['su_limit_hrs']
        if limit in (-1, 0):
            db_table.update(dict(account=arguments['<account>'], date=date.today(), upper_limit_informed=False, max_limit_informed=False),
                        ['account'])

            # Log the action
            log_action(f"Account: {arguments['<account>']} End of Date Update")
        else:
            db_table.update(dict(account=arguments['<account>'], su_limit_hrs=py_sb_settings.DEFAULT_ALLOCATION,
                        date=date.today(), upper_limit_informed=False, max_limit_informed=False), ['account'])
            log_action(f"Account: {arguments['<account>']} End of Date Reset")

        # Reset raw usage
        COMMAND = "sacctmgr -i modify account where account={0} cluster={1} set RawUsage=0"
        for cluster_edl in py_sb_settings.CLUSTERS:
            popen(COMMAND.format(arguments['<account>'], cluster_edl))

elif arguments['get_sus']:
    # Check if database item exists
    check_item_in_table(db_table, arguments['<account>'], 'check')

    # Print out SUs
    STRING = "Account {0} has {1} SUs"
    sus = db_table.find_one(account=arguments['<account>'])['su_limit_hrs']
    print(STRING.format(arguments['<account>'], sus))

elif arguments['release_hold']:
    # Check if database item exists
    check_item_in_table(db_table, arguments['<account>'], 'check')

    # Get the usage from `sshare` for the account and cluster
    COMMAND = "sshare --noheader --account={0} --cluster={1} --format=RawUsage"
    RAWUSAGE = 0
    for cluster_rh in py_sb_settings.CLUSTERS:
        RAWUSAGE += int(popen(COMMAND.format(arguments['<account>'], cluster_rh)).read().split('\n')[1].strip())

    # raw usage is in CPU Seconds
    RAWUSAGE /= (60 * 60)

    # Get limit in database
    limit = db_table.find_one(account=arguments['<account>'])['su_limit_hrs']

    # Make sure raw usage is less than limit
    if int(RAWUSAGE) < limit:
        # Account reached limit, remove hold on account
        COMMAND = "sacctmgr -i modify account where account={0} cluster={1} set "+str(py_sb_settings.ACCOUNT_HOLD)+"=cpu=-1"
        for cluster_rh2 in py_sb_settings.CLUSTERS:
            popen(COMMAND.format(arguments['<account>'], cluster_rh2))

        # Log the action
        log_action(f"Account: {arguments['<account>']} Released Hold")
    else:
        sys.exit("ERROR: The SLURM RawUsage on the account ("+str(RAWUSAGE)+") is larger than the slurm_bank SU limit ("+str(limit)+") ... you'll need to add SUs")

elif arguments['three_month_check']:
    # Check if database item exists
    check_item_in_table(db_table, arguments['<account>'], 'check')

    # Get today's date and end_date from table
    today = date.today()
    begin_date = db_table.find_one(account=arguments['<account>'])['date']

    # End date is the begin_date + 365 days
    end_date = begin_date + timedelta(365)
    delta = end_date - today

    # Make sure limit isn't 0 or -1
    limit = db_table.find_one(account=arguments['<account>'])['su_limit_hrs']

    # If the dates are separated by 90 days and the limits aren't 0 or -1 send an email
    if delta.days == 90 and limit != -1:
        pass
        # *******************INFORM ACTION REQUIRED********************

elif arguments['dump']:
    if not exists(arguments['<filename>']):
        items = db[py_sb_settings.DB_TABLE_NAME].all()
        freeze(items, format='json', filename=arguments['<filename>'])
    else:
        sys.exit(f"ERROR: file {arguments['<filename>']} exists, don't want you to overwrite a backup")

elif arguments['repopulate']:
    if exists(arguments['<filename>']):
        print("DANGER: This function OVERWRITES slurm_bank.db, are you sure you want to do this? [y/N]")
        choice = input().lower()
        if choice in ("yes", "y"):
            # Dump the DB first as a backup method, to file defined in py_settings.py
            items = db[py_sb_settings.DB_TABLE_NAME].all()
            freeze(items, format='json', filename=py_sb_settings.DATABASE_BACKUP_JSON)

            # Get the contents of the supplied dump
            with open(arguments['<filename>'], 'r', encoding="utf8") as json_input_file:
                contents = json.load(json_input_file)

            # Drop the current table and recreate it
            db_table.drop()
            db_table = db[py_sb_settings.DB_TABLE_NAME]

            # Fix the contents['results'] list of dicts
            for item in contents['results']:
                # Python 2.6 doesn't support a read from string for dates
                str_to_int = [int(x) for x in item['date'].split('-')]
                item['date'] = date(str_to_int[0], str_to_int[1], str_to_int[2])
                item['su_limit_hrs'] = int(item['su_limit_hrs'])

            # Insert the list
            db_table.insert_many(contents['results'])
    else:
        sys.exit(f"ERROR: file {arguments['<filename>']} doesn't exist? Can't repopulate from nothing")
