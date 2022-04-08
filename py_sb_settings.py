# Constants/Parameters, modify these

CLUSTERS=['dev'] #(list of slurm clusters, here just one...)
LOGFILE='/var/log/slurm/slurm_bank/slurm_bank.log' #logging (account actions)
DATABASE='/etc/slurm_bank/database/slurm_bank.db' #main working db file
DATABASE_BACKUP_JSON='/etc/slurm_bank/database/slurm_bank.db.json.backup' #backup file, taken on repopulate
DB_TABLE_NAME='sbank' #alternatives to respresent ORG could be "crc", "arc" etc.

DEFAULT_ALLOCATION=1#SU defualt allocation - can't allocate less
PROPOSAL_LENGTH_DAYS=365#duration of the project proposal - can be used for a check
UPPER_LIMIT_PERCENT=90#percent of SUs cosumed upper warning
LOWER_LIMIT_PERCENT=60#percent of SUs cosumed lower warning

ACCOUNT_HOLD='GrpTRESMins' #e.g. alternative is GrpTRESRunMins consult SLURM man page etc.

#EMAIL_FROM #not configured/written
#EMAIL_SERVER_IP #not configured/written
