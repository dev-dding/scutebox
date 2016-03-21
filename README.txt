ScuteBox Setup for Accessing Global Server

There are two pieces of software need to be installed in Scutebox
1. Broadcasting server
2. Internet IP updater

Broadcasting server
1. Copy file ¡°bserver¡± to /usr/sbin/
2. Change it to executable if it is not
3. Copy file ¡°bserver.service¡± to /etc/systemd/system/
4. Run command below
   $ sudo systemctl start bserver.service
   $ sudo systemctl enable berver.service
5. After install all software, change firewall to let data from port 45321 go through
   $ sudo firewall-cmd --permanent --zone=public --add-port=45321/udp
   $ sudo firewall-cmd --reload 

Update Scutebox Internet IP Periodically
1. Copy file ¡±updateip.py¡± to /usr/sbin/ or myOwnCloud executable directory
2. Modify the URL in ¡°updateip.py¡±  from https://64.140.118.221:3322  the real global server address
3. Add the following command to CRONTAB to run every one minute
   python /usr/sbin/updateip.py
