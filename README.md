# slurm_su_bank_python3

# UNDER DEVELOPMENT!!! USE AT OWN RISK

A Banking/Resource Allocation (Service Unit) tracking system for the SLURM job scheduler based upon <i>slurm_bank</i> created by Barry Moore (2017).

Developed on python 3.6.8. Eventual plan to update popen for python 3.7.

# Table of Contents
1. [Why?](#why)
2. [How?](#how)
3. [Prerequisites](#prerequisites)
4. [Accounts and Associations](#accounts-and-associations)
5. [Setup](#setup)
   1. [User](#user) 
   2. [Vars](#vars)
   3. [Charging](#charging)
6. [Usage](#usage)
   1. [Operation](#operation)
   2. [Held accounts](#held-accounts)
   3. [Adding and account](#adding-an-account)
7. [Checking (Cron)](#checking-cron)
8. [Dumping the DB](#dumping-the-db)
9. [Useful SLURM commands](#useful-slurm-commands)


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

- Python3 (tested on 3.6.8)
    - [dataset](https://dataset.readthedocs.io/en/latest/): "databases for lazy people"
    - [docopt](http://docopt.org): "command line arguments parser, that will make you smile"
    - [datafreeze](https://github.com/pudo/datafreeze): Dump (freeze) SQL query results from a database. As per https://dataset.readthedocs.io/en/latest/api.html datafreeze is a seperate module to dataset - See Data Export section.
- Slurm: tested with 19x
- SMTP: NOT required, we plan to use external mechanism for any notifications

# Accounts and Associations 


In your SLURM configuration is envisaged you will form a tree where multiple users are associated with an account (project) e.g.:
```
       Account       User  RawShares  NormShares    RawUsage  EffectvUsage  FairShare 
-------------------------------------------------------------------------------------------------
  test1                       parent    0.025000     2686197      0.999999            
    test1            user1    parent    0.025000           0      0.000000   0.545455 
    test1            user2    parent    0.025000     2587994      0.963441   0.545455 
    test1            user3    parent    0.025000       98202      0.036558   0.545455 
```
Above we see the test1 account has user members user{1..3}. Usage by submitted user jobs on the test1 account will propogate/accumulate, and in this example it'll be test1's SUs in the bank/DB that will be compared to the overall <b>RawUsage</b> stored by SLURM accounting.

# Setup

## User

Clone this repo/code on the SLURM master node. e.g. into a new directory, /etc/slurm_bank. Make ownership and user of program the slurm user (not root!).

## Vars

- <b><i>py_sb_settings.py</i></b> is used to set the bank's behaviour and file locations for the python code.
- <b><i>env.sh</i></b> is used primarily to setup vars for slurm_bank_cron.sh cron checks. It also is used by the db_print.sh script.

## Charging

In SLURM you will need to setup billing per partition (slurm.conf) e.g. within partition definition:
<br><br>
Example compute:<br>
```TRESBillingWeights="CPU=1.0,Mem=0.25G,GRES/gpu=0.0"```<br>
Example GPU:<br>
```TRESBillingWeights="CPU=1.0,Mem=0.25G,GRES/gpu=1.0"```

Here, CPU=1.0 means 1 service unit per hour to use 1 core and GRES/gpu=1.0 means 1 service unit per hour to use 1 GPU card.

# Usage

## Operation

After setup of ```py_sb_settings.py``` and ```env.sh``` ...

Typically most operations will take place through ```slurm_bank_cron.sh``` cron checks.

```slurm_bank.py``` is used to manage/view SU balances for accounts stored in the DB and to release (account exceeded SUs).

```db_print.sh``` is a simple script that'll quickly tell you what's going on overall by printing the entire DB table. Also consult the cron logs.

## Held accounts

An account will be held if RawUsage exceeds the SUs in the bank DB.

If the account is held in SLURM you'll see an entry in the GrpTRESMins column e.g.:

```
           Account       User  RawShares  NormShares    RawUsage  EffectvUsage  FairShare                    GrpTRESMins 
------------------------------------------------------------------------------------------------------------------------ 
 test1                           parent    0.025000     2686197      0.999999                                     cpu=0 
    test1              user1     parent    0.025000           0      0.000000   0.545455                                
    test1              user2     parent    0.025000     2587994      0.963441   0.545455                                
    test1              user3     parent    0.025000       98202      0.036558   0.545455                                
```

## Adding an account:

To add an account and SUs you simply execute ```slurm_bank.py``` e.g.

```
./slurm_bank.py insert test1 10000
```

Querying immediately after would look like this:

```
./slurm_bank.py get_sus test1
Account test1 has 10000 SUs
```

The resultant DB entry would look like this:<br>

```1|test1|10000|2022-04-08|0|0|0```


# Checking (Cron)

The script ```slurm_bank_cron.sh``` will perform a check of Service Units by looping through all users - it is anticipated you'd run this at very least daily. If a user has exhausted their SUs they will be held. The mechanism to hold we will use is by setting the account's <b>GrpTRESMins</b> in SLURM to hold the account. This can be changed in ```py_sb_settings.py```

# Dumping the DB

You can dump the DB to JSON and subsequently repopulate it. On repopulating a backup JSON dump is now taken to a fixed path - the path is set in ```py_sb_settings.py```

Additionally you can dump to csv, but JSON is currently required to repopulate the sqlite DB, which is required for operation of the bank.

# Useful SLURM commands

See the tree of accounts and show GrpTRESMins to see if any are held.

```sacctmgr show assoc tree -o format=account,user,share,GrpTRESMins```

See RawUsage and Share information for accounts. Also show GrpTRESMins.

```sshare -a -o Account,User,RawShares,NormShares,RawUsage,EffectvUsage,FairShare,GrpTRESMins```

Billing rate for running job <jobID>

```scontrol show job <jobID> | grep -i billing```
 
Billing rate for completed job <jobID>

```sacct -X --format=AllocTRES%80,Elapsed -j <jobID>```
