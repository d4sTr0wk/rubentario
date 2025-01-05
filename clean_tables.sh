#!/bin/bash

echo "Cleaning tables PostgreSQL . . ."

if [ "$#" -ne 1 ]; then
	echo "Usage: ./clean_tables.sh <db_name>"
	exit 1
fi

DB_NAME="$1_warehouse"
DB_USER="rubentario"
DB_PASS="rubentario"

PGPASSWORD=$DB_PASS psql -U $DB_USER -d $DB_NAME -c "DROP TABLE inventory CASCADE;"
PGPASSWORD=$DB_PASS psql -U $DB_USER -d $DB_NAME -c "DROP TABLE products CASCADE;"
PGPASSWORD=$DB_PASS psql -U $DB_USER -d $DB_NAME -c "DROP TABLE transactions CASCADE;"
PGPASSWORD=$DB_PASS psql -U $DB_USER -d $DB_NAME -c "DROP TABLE requests CASCADE;"

echo "Tables dropped!✅"
