#!/bin/bash
#
echo "Installing PostgreSQL . . ."
sudo apt install postgresql postgresql-contrib -y

echo "Starting and enabling PostgreSQL service . . ."
sudo systemctl start postgresql
sudo systemctl enable postgresql

DB_NAME="warehouse"
DB_USER="rubentario"
DB_PASS="rubentario"

# Create DB
echo "Creating DataBase $DB_NAME . . ."
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"

# Create user
echo "Creating user $DB_USER . . ."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
sudo -u postgres psql -c "ALTER DATABASE $DB_NAME OWNER TO $DB_USER;"

# Grant privileges to the user
echo "Granting privileges to $DB_USER on $DB_NAME . . ."
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

echo "Database $DB_NAME and user $DB_USER created successfully!"
