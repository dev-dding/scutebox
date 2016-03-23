#!/bin/bash

if [ $1 == "build" ]; then
    echo "building broadcast server from source code"
    gcc bserver.c -o bserver
    gcc bclient.c -o bclient
fi

if [ $1 == "install" ]; then
   # Make sure only root can run our script
   if [[ $EUID -ne 0 ]]; then
      echo "Install script must be run as root" 1>&2
      exit 1
   fi
   systemctl stop bserver
   cp bserver /usr/local/bin/
   cp bserver.service /etc/systemd/system/
   cp updateip.py /usr/local/bin/
   systemctl daemon-reload
   systemctl restart bserver
fi

