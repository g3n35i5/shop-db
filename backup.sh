#!/usr/bin/sh
currentDatabase="./shop.db"
backupName=./backups/database_`date "+%d-%m-%Y_%H-%M"`.dump
if [ -f "$currentDatabase" ]
then
  echo "$currentDatabase found."
  echo "copy to $backupName"
  sqlite3 shop.db .dump > $backupName
  if [ -f "$backupName" ]
  then
    echo "success"
  else
    echo "!!!!!!!!!! AHHHH FUCK !!!!!!!!!!"
  fi
else
  echo "$currentDatabase not found."
fi
