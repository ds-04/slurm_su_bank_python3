#Associations to work with - prefix
PROJECT_PREFIX="" #used by grep - slurm project group name e.g. resXXXX, seen in associations
#Where the scripts are stored
script_home=/etc/slurm_bank
#Where logs from cron invocation of program should go
cron_log_dir=/var/log/slurm/slurm_bank
#Utilities
SACCTMGR=/usr/bin/sacctmgr
GREP=/usr/bin/grep
