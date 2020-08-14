#! /bin/bash

echo "[datacube]" > ~/.datacube.conf
echo "db_hostname: ${DB_HOSTNAME}" >> ~/.datacube.conf
echo "db_database: ${DB_DATABASE}" >> ~/.datacube.conf
echo "db_username: ${DB_USER}" >> ~/.datacube.conf
echo "db_password: ${DB_PASSWORD}" >> ~/.datacube.conf

datacube system init

exec $@