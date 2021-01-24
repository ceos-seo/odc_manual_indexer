#! /bin/bash

echo "[datacube]" > ~/.datacube.conf
echo "db_hostname: ${ODC_DB_HOSTNAME}" >> ~/.datacube.conf
echo "db_database: ${ODC_DB_DATABASE}" >> ~/.datacube.conf
echo "db_username: ${ODC_DB_USER}" >> ~/.datacube.conf
echo "db_password: ${ODC_DB_PASSWORD}" >> ~/.datacube.conf
cp ~/.datacube.conf /etc/datacube.conf

datacube system init

exec $@