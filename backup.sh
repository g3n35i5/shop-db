#!/usr/bin/sh
currentDatabase="/root/shop-db-backend/shop.db"
backupName=/root/backups/database/database_`date "+%d-%m-%Y_%H-%M"`.dump
if [ -f "$currentDatabase" ]
then
  echo "$currentDatabase found."
  echo "copy to $backupName"
  sqlite3 /root/shop-db-backend/shop.db .dump > $backupName
  if [ -f "$backupName" ]
  then
    echo "success"
  else
    echo "!!!!!!!!!! AHHHH FUCK !!!!!!!!!!"
  fi
else
  echo "$currentDatabase not found."
fi
