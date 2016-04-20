#!/bin/bash
cd "$(dirname "$0")"

ROOT_UID=0     # Only users with $UID 0 have root privileges.
E_NOTROOT=87   # Non-root exit error.

# Make sure only root can run this script
if [ "$UID" -ne "$ROOT_UID" ]
then
   echo "Must be root to run this script."
   exit $E_NOTROOT
fi  

# stop bserver.service if it is running
pidof  bserver >/dev/null
if [[ $? -ne 0 ]] ; then
   echo "Stopping bserver.service"
   systemctl stop bserver
   sleep 1
fi

# copy files to proper directories
echo "Copy files to destination directories"
cp -f ./bserver /usr/local/sbin/bserver
cp -f ./bserver.service /etc/systemd/system/bserver.service
cp -f ./updateip.py /usr/local/sbin/updateip.py

# reload daemons
systemctl daemon-reload
sleep 1

# start service and configure for auto-start on reboot
echo "Starting broadcast server service"
systemctl start bserver
systemctl enable bserver

# Open port for listening UDP broadcasting message
echo "Adding UDP port for broadcasting server"
firewall-cmd --permanent --zone=public --add-port=45321/udp
firewall-cmd --reload 

# Add scheduled task every minute to update scute IP address
# task is saved to scutecron file
echo "Adding updateip to crontab"
crontab -l | sed 'updateip.py/d' > /tmp/cron.tmp
cat scute.cron >> /tmp/cron.tmp
crontab /tmp/cron.tmp
rm -rf /tmp/cron.tmp

exit 0

