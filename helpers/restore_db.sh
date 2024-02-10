#!/bin/bash

echo "[+] Reading env.conf"

echo "Please enter mysqldump to restore:"
read filename

echo "Please enter password for db root:"
read -s password

echo "[+] Please enter db root password:"
/usr/bin/docker exec -i kinderbasar-db-1 /bin/sh -c "/usr/bin/mysql -u root -p$password kinderbasar" < $filename

echo "[+] Done"