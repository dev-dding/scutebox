#!/usr/bin/env python  
# -*- coding:UTF-8 -*-  

import os
import urllib2
import logging
import logging.handlers
import subprocess
import json
import socket

key = "scutekey_001"
old_global_ip_file = "/tmp/scute_global_ip"
old_local_ip_file = "/tmp/scute_local_ip"
gs_url = "https://64.140.118.221:3443/updatescuteip.php"

def getLocalNetworkIp():
    # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # s.connect(("yahoo.com",80))
    # str = s.getsockname()[0]
    # s.close()

    # Get IP address from "ip addr" command
    str = "ip addr | grep 'state UP' -A2 | grep inet | awk '{print $2}' | cut -f1 -d'/'"
    p = subprocess.Popen([str], shell=True, stdout=subprocess.PIPE)
    str = p.stdout.read()

    return str

def validateip( ip ):
    try:
        parts = ip.split('.')
        return len(parts) == 4 and all(0 <= int(part) < 256 for part in parts)
    except ValueError:
        return False # one of the 'parts' not convertible to integer
    except (AttributeError, TypeError):
        return False # `ip` isn't even a string

def GetScuteConfigData():
    fo = open("/tmp/getscutecfg.php", "wb")
    fo.write("<?php\n")
    fo.write("include \'/var/www/scute/config/config.php\';\n")
    fo.write("echo \'{\"scuteid\":\"\' . $CONFIG[\'instanceid\'] . \'\"}\';\n")
    fo.write("?>\n")
    fo.close()
    p = subprocess.Popen(["php /tmp/getscutecfg.php"], shell=True, stdout=subprocess.PIPE)
    ret = p.stdout.read()
    return ret


# get the router internet ip address by running wget command
def GetGlobalIP():
    # os.system('wget -qO- http://ipecho.net/plain > ipaddr.txt')
    str = "wget -qO- --tries=2 --timeout=2 http://ipecho.net/plain"
    p = subprocess.Popen([str], shell=True, stdout=subprocess.PIPE)
    ret = p.stdout.read()
    return ret


# prepare for logging messages to syslog
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
handler = logging.handlers.SysLogHandler(address = '/dev/log')
formatter = logging.Formatter('%(module)s: %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)

# get and validate the router internet ip address
new_ext_ip = GetGlobalIP()
if not validateip( new_ext_ip ) :
    print "*** ERROR ***  Cannot get valid Internet IP address"
    log.info('Cannot get valid Internet IP address')
    new_ext_ip = ""
    # Remove the old file if Internet is not connected
    if os.path.isfile(old_global_ip_file) :
        os.remove(old_global_ip_file)
    # quit()


# Get global IP address from previous data which is saved to old_global_ip_file
old_ext_ip = ""
if not os.path.isfile(old_global_ip_file) :
    log.info('Previous global IP file not existing')
    # print "Previous global IP file not existing"
    # os.system("touch %s" % old_global_ip_file)
else :
    try :
        f_old = open(old_global_ip_file,"r")
        old_ext_ip = f_old.readline()
        f_old.close()
        old_ext_ip = old_ext_ip.strip('\n')   # remove the line end
        old_ext_ip = old_ext_ip.strip('\r')
    except :
        log.critical('File access error -> ipaddr.old')
        # print "File access error -> ipaddr.old"

# Get local IP address from previous data which is saved to old_local_ip_file
oldlocalip = ""
if not os.path.isfile(old_local_ip_file) :
    log.info('Previous local IP file not existing')
    # print "Previous local IP file not existing"
    # os.system("touch %s" % old_local_ip_file)
else :
    try :
        f_old = open(old_local_ip_file,"r")
        oldlocalip = f_old.readline()
        f_old.close()
        oldlocalip = oldlocalip.strip('\n')   # remove the line end
        oldlocalip = oldlocalip.strip('\r')
    except :
        log.critical('File access error -> ipaddr.old')
        # print "File access error -> ipaddr.old"

############################################################################
# get local network ip address
# add trusted domain if localip has been changed
############################################################################
localip = getLocalNetworkIp()

# It might have two ethernet cards with valid ip address
# Make array for multiple ethernet cards
localip = localip.split('\n')

# set update domain configure flag
resetDomainConfig = False

str = ""
for ip in localip :
    if ip :
        if not ip in oldlocalip :
            # Add trust domain when internal or external ip change
            resetDomainConfig = True
            print "New local ip " + ip
        else :
            print "Internal IP no change"

        # make string for new ip address
        str = str + ip + "  "
    else :
        print "Ignore empty IP string"

# Save the local ips to file when it changes
if resetDomainConfig :
    f_old = open(old_local_ip_file, "w+")
    f_old.write(str)
    f_old.close()
    print str

if new_ext_ip != old_ext_ip :
    # Add trust domain when internal or external ip change
    resetDomainConfig = True

    # reading scuteID and scutebox port forwarding from scutebox config file
    str = GetScuteConfigData()
    cfg_data = json.loads( str )
    port = "14443"  # cfg_data['port']
    scuteid = cfg_data['scuteid']
    if not port:
        port = "14443"
        # log.info('There is no valid port number in config file')
        # quit()
    if not scuteid:
        scuteid =  "SB-0001"
        # log.info('There is no valid scuteid in config file')
        # quit()
    #
    # get local network ip address
    # localip = getLocalNetworkIp()
    #
    # making URL for updating IP to global server
    url_update = gs_url + '?ip=' + new_ext_ip + '&scuteid=' + scuteid + '&key=' + key + '&port=' + port + '&localip=' + localip[0]
    # print url_update
    res = urllib2.urlopen( url_update )
    #
    str = res.read()
    # print str
    res_data = json.loads( str )
    #
    # verify updating result
    if res_data['result'] == "true" :
        # print "result: " + res_data['result']
        # print "status: " + res_data['status']
        cmd = 'echo ' + new_ext_ip + ' > ' + old_global_ip_file
        os.system( cmd )
    	log.info( 'updated IP to global server successfully' )
    else :
    	log.error('failed to update IP to global server, ' + res_data['status'])
else :
    # log.info('IP Address no change')
    print "External IP Address no change"

# Add new IPs to domain config file
if resetDomainConfig :
    os.system("sudo -u apache /var/www/scute/occ cicer:domains --clear")
    print "Clear domains"
    if new_ext_ip :
        os.system("sudo -u apache /var/www/scute/occ cicer:domains --add %s" % new_ext_ip)
        print new_ext_ip
    for ip in localip :
        if ip :
            os.system("sudo -u apache /var/www/scute/occ cicer:domains --add %s" % ip)
            print ip
    log.info('Added trust domain due to external ip change')

