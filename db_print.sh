#!/bin/bash
#Basic utility script to quickly print the DB table

#Grab settings from py_sb_settings.py
DATABASE_PATH=`egrep "DATABASE(\s)?*=" ./py_sb_settings.py | cut -d "=" -f2 | cut -d\' -f2`
#echo $DATABASE_PATH debug only
TABLE_NAME=`egrep "DB_TABLE_NAME(\s)?*=" ./py_sb_settings.py | cut -d "=" -f2 | cut -d\' -f2`


echo "Print schema of ${TABLE_NAME} table from ${DATABASE_PATH}"
echo ""
sqlite3 -batch ${DATABASE_PATH} ".schema ${TABLE_NAME}"
echo ""
echo "----------------------------------------"
echo "Print all entires from table ${TABLE_NAME}"
echo ""
sqlite3 -batch ${DATABASE_PATH} "select * from ${TABLE_NAME}"
