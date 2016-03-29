#!/bin/bash

ROOT_UID=0     # Only users with $UID 0 have root privileges.
E_NOTROOT=87   # Non-root exit error.

if [ "$#" -gt 1 ]; then
    echo "Invalid parameter"
    echo "Usage:     ./make_install.sh"
    echo "           ./make_install.sh  install"
    echo ""
    exit 1
elif [[ "$#" -eq 1 && "$1" != "install" ]]
then
    echo "Invalid parameter 1"
    echo "Usage:     ./make_install.sh"
    echo "           ./make_install.sh  install"
    echo ""
    exit 1
fi

if [ "$#" -eq 0 ]; then
    echo "Building broadcast server from source code ..."
    if [ ! -f "./bserver.c" ]; then
        echo "Missing bserver.c"
        exit 1
    else
        gcc bserver.c -o bserver
    fi
    if [ ! -f "./bclient.c" ]; then
        echo "Missing bclient.c"
        exit 1
    else
        gcc bclient.c -o bclient
    fi
    echo "Done."
    exit
elif [ "$1" == "install" ]; then
   # Make sure only root can run this script
   if [ "$UID" -ne "$ROOT_UID" ]
   then
      echo "Must be root to run this script."
      exit $E_NOTROOT
   fi  

   #if [[ $EUID -ne 0 ]]; then
   #   echo "Install script must be run as root" 1>&2
   #   exit 1
   #fi

   # stop bserver.service if it is running
   pidof  bserver >/dev/null
   if [[ $? -ne 0 ]] ; then
       echo "Stop broadcast server"
       systemctl stop bserver
       sleep 1
   fi

   # copy files to proper directories
   echo "Copy files to destination directories"
   cp -f ./bserver /usr/local/bin/bserver
   cp -f ./bserver.service /etc/systemd/system/bserver.service
   cp -f ./updateip.py /usr/local/bin/updateip.py

   # reload daemons
   systemctl daemon-reload
   sleep 1

   # start service and configure for auto-start on reboot
   echo "Start broadcast server"
   systemctl start bserver
   systemctl enable bserver

   # Open port for listening UDP broadcasting message
   echo "Adding UDP port for broadcasting server"
   firewall-cmd --permanent --zone=public --add-port=45321/udp
   firewall-cmd --reload 

   # Add scheduled task every minute to update scute IP address
   # task is saved to scutecron file
   echo "Adding updateip to crontab"
   crontab scute.cron

   exit 0
fi

