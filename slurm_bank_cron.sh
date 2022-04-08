#!/usr/bin/env bash

#1) check SUs
#2) check end dates
#3) check three-month

source env.sh

slurm_bank="${script_home}/slurm_bank.py"
cron_logs="${cron_log_dir}/cron.log"

# generate a list of all of the accounts, filter if prefix defined
if [ -z "${PROJECT_PREFIX}" ]
then
      accounts=($($SACCTMGR list accounts -n format=account%30))
else
      accounts=($($SACCTMGR list accounts -n format=account%30 | $GREP $PROJECT_PREFIX))
fi

INVOCATION_TIME=`date +%d-%m-%Y-%T`

echo "--------${INVOCATION_TIME}--------" >> $cron_logs

for i in ${accounts[@]}; do
    if [ $i != "root" ]; then
        ${slurm_bank} check_service_units_limit $i >> $cron_logs 2>&1  # check SUs used
        #${slurm_bank} check_end_of_date_limit $i >> $cron_logs 2>&1   # optional
        #${slurm_bank} three_month_check $i >> $cron_logs 2>&1         # optional
    fi
done

echo "-------END--------" >> $cron_logs
