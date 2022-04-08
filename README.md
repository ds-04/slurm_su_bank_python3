# slurm_su_bank_python3

A Banking/Resource Allocation (Service Unit) tracking system for SLURM based upon <i>slurm_bank</i> created by Barry Moore (2017).


# Table of Contents
1. [Why?](#why)
2. [How?](#how)
3. [Prerequisites](#prerequisites)
4. [Accounts and Associations](#accounts)
5. [Setup](#setup)
6. [Usage](#usage)
7. [Checking (Cron)](#checking-cron)


# Why?

We needed a banking system for SLURM, which is simple and robust - Barry Moore's <i>slurm_bank</i> met this criteria, work was undertaken to build upon it to create this project.

In this version python3 updates have been made and <b>email notifications from the program itself are currently removed</b>.

<b>Why are email notifications removed?</b> We plan to use another (external) system to keep track of project proposal end date and to email upon thresholds.


# How?

Using the existing associations in your Slurm database, we use the "RawUsage"
from `sshare` to monitor service units (CPU hours) on the cluster. From the documentation:

``` text
Raw Usage
The number of cpu-seconds of all the jobs that charged the account by the user.
This number will decay over time when PriorityDecayHalfLife is defined

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
PriorityDecayHalfLife=0-00:00:00
PriorityUsageResetPeriod=NONE
```

The `slurm_bank.py` takes care of resetting "RawUsage" for you. The bank enforces
two limits:

1. A service unit limit: How many compute hours is an account allowed
   to use? <b>ENFORCED</b>
2. A date limit: How long does the proposal last? <b>NOT ENFORCED, BUT CAPABILITY IS RETAINED</b>. We plan to manage this elsewhere.

The bank's three month check (check 90 days before project end) is dormant here. Again we plan to check externally. 


# Prerequisites

- Python3
    - [dataset](https://dataset.readthedocs.io/en/latest/): "databases for lazy people"
    - [docopt](http://docopt.org): "command line arguments parser, that will make you smile"
- Slurm: tested with 19x
- SMTP: not required, we plan to use external mechanism for any notifications

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

- py_sb_settings.py is used to set the bank's behaviour and file locations for the python code.
- env.sh is used primarily to setup vars for slurm_bank_cron.sh cron checks. It also is used by the db_print.sh script.

# Usage

After setup py_sb_settings.py and env.sh...

Typically most operations will take place through slurm_bank_cron.sh cron checks.

slurm_bank.py is used to change SU balances and to release.


# Checking (Cron)

The script <i>slurm_bank_cron.sh</i> will perform a check of Service Units by looping through all users. If a user has exhausted their SUs they will be held. The mechanism to hold we will use is by setting the account's GrpTRESMins to hold the account. This can be changed in py_sb_settings.py
