# slurm_su_bank_python3

# UNDER DEVELOPMENT!!! USE AT OWN RISK

A Banking/Resource Allocation (Service Unit) tracking system for the SLURM job scheduler based upon <i>slurm_bank</i> created by Barry Moore (2017).


# Table of Contents
1. [Why?](#why)
2. [How?](#how)
3. [Prerequisites](#prerequisites)
4. [Accounts and Associations](#accounts-and-associations)
5. [Setup](#setup)
6. [Usage](#usage)
7. [Checking (Cron)](#checking-cron)


# Why?

We needed a banking system for SLURM, which is simple and robust - Barry Moore's <i>slurm_bank</i> met this criteria, work was undertaken to build upon it to create this project.

In this version python3 updates have been made and <b>email notifications from the program itself are currently removed</b>.

<b>Why are email notifications removed?</b> We plan to use another (external) system to keep track of project proposal end date and to email upon thresholds.


# How?

A Python program is used and data stored in an sqlite file.

Using the existing associations in your SLURM database, we use the <b>RawUsage</b>
from `sshare` to monitor service units (CPU hours) on the cluster. From the documentation:

``` text
Raw Usage
The number of cpu-seconds of all the jobs that charged the account by the user.
This number will decay over time when PriorityDecayHalfLife is defined.

PriorityDecayHalfLife
This controls how long prior resource use is considered in determining how
over- or under-serviced an association is (user, bank account and cluster) in
determining job priority. The record of usage will be decayed over time, with
half of the original value cleared at age PriorityDecayHalfLife. If set to 0 no
decay will be applied. This is helpful if you want to enforce hard time limits
per association. If set to 0 PriorityUsageResetPeriod must be set to some
interval.
```

Therefore, in your Slurm configuration you will need:

``` text
PriorityDecayHalfLife=0-00:00:00 #No decay will be applied. This is helpful if you want to enforce hard time limits per association.
PriorityUsageResetPeriod=NONE #Never clear historic usage. The default value.
AccountingStorageEnforce=associations,limits,qos,safe #If you don't set the configuration parameters that begin with "AccountingStorage" then accounting information will not be referenced or recorded
```

The `slurm_bank.py` takes care of resetting SLURM'S <b>RawUsage</b> for you upon the account in question. The bank enforces
two limits:

1. A service unit limit: How many compute hours is an account allowed
   to use? <b>ENFORCED</b> by default (cron script)
2. A date limit: How long does the proposal last? <b>NOT ENFORCED (via cron script), BUT CAPABILITY IS RETAINED</b>. We plan to manage this elsewhere.

Other:

- The bank's three month check (check 90 days before project end) is dormant here. Again, we plan to check externally. 
- Upper and lower SU check limits are defined, these don't result in an email but do result in DB value change. Again, we plan to mail externally.


# Prerequisites

- Python3
    - [dataset](https://dataset.readthedocs.io/en/latest/): "databases for lazy people"
    - [docopt](http://docopt.org): "command line arguments parser, that will make you smile"
- Slurm: tested with 19x
- SMTP: NOT required, we plan to use external mechanism for any notifications

# Accounts and Associations 


It is envisaged you will form a tree e.g.:
```
  test1                       parent    0.025000     2686197      0.999999            
    test1            user1    parent    0.025000           0      0.000000   0.545455 
    test1            user2    parent    0.025000     2587994      0.963441   0.545455 
    test1            user3    parent    0.025000       98202      0.036558   0.545455 
```
Above we see the test1 account has user members user{1..3}. Usage and Service Units will propogate.

# Setup

- <b><i>py_sb_settings.py</i></b> is used to set the bank's behaviour and file locations for the python code.
- <b><i>env.sh</i></b> is used primarily to setup vars for slurm_bank_cron.sh cron checks. It also is used by the db_print.sh script.


# Usage

After setup of ```py_sb_settings.py``` and ```env.sh``` ...

Typically most operations will take place through ```slurm_bank_cron.sh``` cron checks.

```slurm_bank.py``` is used to manage/view SU balances for accounts stored in the DB and to release (account exceeded SUs).

```db_print.sh``` is a simple script that'll quickly tell you what's going on overall by printing the entire DB table. Also consult the cron logs.


## ADDING AN ACCOUNT TO THE BANK:

To add an account and SUs you simply execute ```slurm_bank.py``` e.g.

```
./slurm_bank.py insert test1 10000
```

Querying immediately after would look like this

```
./slurm_bank.py get_sus test1
Account test1 has 10000 SUs
```

The resultant DB entry would look like this:<br>

```1|test1|10000|2022-04-08|0|0|0```


# Checking (Cron)

The script ```slurm_bank_cron.sh``` will perform a check of Service Units by looping through all users. If a user has exhausted their SUs they will be held. The mechanism to hold we will use is by setting the account's <b>GrpTRESMins</b> in SLURM to hold the account. This can be changed in ```py_sb_settings.py```
