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
oldip = "/tmp/scute_global_ip"
gs_url = "https://64.140.118.221:3443/updatescuteip.php"

# from http://commandline.org.uk/python/how-to-find-out-ip-address-in-python/
def getLocalNetworkIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("yahoo.com",80))
    str = s.getsockname()[0]
    s.close()
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
    fo.write("echo \'{\"scuteid\":\"\' . $CONFIG[\'scuteid\'] . \'\", \"port\":\"\' . $CONFIG[\'port\'] . \'\"}\';\n")
    fo.write("?>\n")
    fo.close()
    p = subprocess.Popen(["php /tmp/getscutecfg.php"], shell=True, stdout=subprocess.PIPE)
    ret = p.stdout.read()
    return ret


# get the router internet ip address by running wget command
def GetGlobalIP():
    # os.system('wget -qO- http://ipecho.net/plain > ipaddr.txt')
    p = subprocess.Popen(["wget -qO- http://ipecho.net/plain"], shell=True, stdout=subprocess.PIPE)
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
newline = GetGlobalIP()
if not validateip( newline ) :
    log.info('Cannot get valid Internet IP address')
    quit()

# Get IP address from previous data which is saved to ipaddr.old
oldline = ""
if not os.path.isfile(oldip) :
    log.info('Previous IP file not existing')
    # print "Previous IP file not existing"
    # os.system("touch %s" % oldip)
else :
    try :
        f_old = open(oldip,'r')
        oldline = f_old.readline()
        f_old.close()
        oldline = oldline.strip('\n')   # remove the line end
        oldline = oldline.strip('\r')
    except :
	    log.critical('File access error -> ipaddr.old')
        # print "File access error -> ipaddr.old"

if newline != oldline :
    # reading scuteID and scutebox port forwarding from scutebox config file
    str = GetScuteConfigData()
    cfg_data = json.loads( str )
    port = cfg_data['port']
    scuteid = cfg_data['scuteid']
    if not port:
        port = "14432"
        # log.info('There is no valid port number in config file')
        # quit()
    if not scuteid:
        scuteid =  "SB-0001"
        # log.info('There is no valid scuteid in config file')
        # quit()
    #
    # get local network ip address
    localip = getLocalNetworkIp()
    #
    # making URL for updating IP to global server
    url_update = gs_url + '?ip=' + newline + '&scuteid=' + scuteid + '&key=' + key + '&port=' + port + '&localip=' + localip
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
        cmd = 'echo ' + newline + ' > ' + oldip
        os.system( cmd )
    	log.info( 'updated IP to global server successfully' )
    else :
    	log.error('failed to update IP to global server, ' + res_data['status'])
else :
    # log.info('IP Address no change')
    print "IP Address no change"
    

