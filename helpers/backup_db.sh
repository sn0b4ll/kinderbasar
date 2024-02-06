#!/bin/bash

echo "[+] Reading env.conf"

filename=$(date +%Y-%m-%d_%H:%M:%S)-backup.sqldump

echo "[+] Please enter db root password:"
/usr/bin/docker exec -it kinderbasar_db_1 /bin/sh -c "/usr/bin/mysqldump -u root -p kinderbasar" > db/backup/$filename
/usr/bin/chmod a-r db/backup/$filename

echo "[+] Done"