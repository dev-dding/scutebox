===================================================================================
                   Broadcast Server Configuration on ScuteBox
===================================================================================

There are two pieces of software need to be installed in Scutebox
1. Broadcasting server
2. Internet IP updater

To Build binary file from source, run script below.
It will compile bserver.c and bclient.c. 
bclient is a debugging tool

# sudo ./make_install.sh


Install broadcast server and UP updater script.

# sudo ./make_install.sh install


Install will do the followings:
1. Copy file "bserver" to /usr/local/bin/
2. Copy file "bserver.service" to /etc/systemd/system/
3. Start bserver service and set it to autorun on boot
   $ sudo systemctl start bserver.service
   $ sudo systemctl enable berver.service
4. After install all software, change firewall to let data go through on port 45321
   $ sudo firewall-cmd --permanent --zone=public --add-port=45321/udp
   $ sudo firewall-cmd --reload 
5. Copy file "updateip.py" to /usr/local/bin/
6. Update Scutebox Internet IP Periodically
   $ crontab scute.cron
