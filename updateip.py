#!/usr/bin/env python  
# please choose encoding type, ascii or UTF-8  
# -*- coding:UTF-8 -*-  

import os
import urllib2
import logging
import logging.handlers
import subprocess
import json
import socket

key = "scutekey_001"
uploadGsGood = "/tmp/scute_gs_success"
gs_url = "https://gs1.scuteworld.com:3443/updatescuteip.php"
localip_inet = ""
scute_id = ""
scute_port = ""
trusted_sites = []

def logMessages( str ):
    log.info( str )
    print str

def getLocalNetworkIp():
    # Get IP address from "ip addr" command
    str = '/usr/sbin/ip addr | grep \'state UP\' -A2 | grep inet | awk \'{print $2}\' | cut -f1 -d\'/\''
    # str = 'cat ipaddr | grep \'state UP\' -A2 | grep inet | awk \'{print $2}\' | cut -f1 -d\'/\''
    p = subprocess.Popen(str, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    str = p.stdout.read().splitlines()
    return str


def validateIp( ip ):
    try:
        parts = ip.split('.')
        return len(parts) == 4 and all(0 <= int(part) < 256 for part in parts)
    except ValueError:
        return False # one of the 'parts' not convertible to integer
    except (AttributeError, TypeError):
        return False # `ip` isn't even a string

def getScuteConfigData():
    fo = open("/tmp/getscutecfg.php", "wb")
    fo.write("<?php\n")
    fo.write("include \'/var/www/scute/config/config.php\';\n")
    fo.write("$len = count($CONFIG[\'trusted_domains\']);\n")
    fo.write("$str = \'[\"\';\n")
    fo.write("for($x = 0; $x < $len; $x++) {\n")
    fo.write("    $str .= $CONFIG[\'trusted_domains\'][$x];\n")
    fo.write("    if ( $x < $len-1 ){\n")
    fo.write("        $str .= \'\", \"\';\n")
    fo.write("    }else{\n")
    fo.write("        $str .= \'\"]\';\n")
    fo.write("    }\n")
    fo.write("}\n")
    fo.write("echo \'{\"scuteid\":\"\' . $CONFIG[\'instanceid\'] . \'\", \"trustedsites\":\' . $str . \'}\';\n")
    fo.write("?>\n")
    fo.close()
    p = subprocess.Popen(["php /tmp/getscutecfg.php"], shell=True, stdout=subprocess.PIPE)
    ret = p.stdout.read()
    return ret

# get the router internet ip address by running wget command
def getGlobalIp():
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
logMessages( "===============  UpdateIP.py Start ===============" )

# get and validate the router internet ip address
new_ext_ip = getGlobalIp()
if not validateIp( new_ext_ip ) :
    logMessages('*** ERROR *** Cannot get valid Internet IP address')
    new_ext_ip = ""
else :
    logMessages( "Internet IP : " + new_ext_ip )
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("yahoo.com",80))
    localip_inet = s.getsockname()[0]
    logMessages( "Local IP to internet : " + localip_inet )
    s.close()

# Get local IP address
localip = getLocalNetworkIp()
logMessages( localip )

# Get local IP address from network settings
cfg_json = getScuteConfigData()
cfg_data = json.loads( cfg_json )
scute_id = cfg_data['scuteid']
logMessages( "Scute ID : " + scute_id )
trusted_sites = cfg_data['trustedsites']
logMessages( trusted_sites )
# scute_port = cfg_data['port']
if not scute_port:
    scute_port = "14443"
if not scute_id:
    scute_id =  "SB-0001"

# set update domain configure flag
resetDomainConfig = False

if not new_ext_ip in trusted_sites :
    logMessages( new_ext_ip + " is not in trusted_sites" )
    resetDomainConfig = True
else :
    logMessages( new_ext_ip + " is in trusted_sites already. :-)" )

for ip in localip :
    if ip :
        if not ip in trusted_sites :
            # Add trust domain when internal or external ip change
            logMessages( ip + " is not in trusted_sites" )
            resetDomainConfig = True
        else :
            logMessages( ip + " is in trusted_sites already. :-)" )
    else :
        logMessages( "Ignore empty IP string" )

# Add new IPs to domain config file
if resetDomainConfig :
    logMessages( "Clear Trusted Domains" )
    str = "sudo -u apache /var/www/scute/occ cicer:domains --clear"
    os.system( str )
    if new_ext_ip :
        logMessages( new_ext_ip + " is added to Trusted Domains" )
        str = "sudo -u apache /var/www/scute/occ cicer:domains --add %s" % new_ext_ip
        os.system( str )
    for ip in localip :
        if ip :
            logMessages( ip + " is added to Trusted Domains" )
            str = "sudo -u apache /var/www/scute/occ cicer:domains --add %s" % ip
            os.system( str )
    #
    # remove the upload successful flag to force update
    cmd = '/bin/rm -rf ' + uploadGsGood
    os.system( cmd )


# Remove the old file if Internet is not connected
if os.path.isfile( uploadGsGood ) :
    logMessages( "Upload file exist" )
    needUploadGs = False
else :
    logMessages( "***  Upload file not exist ***" )
    needUploadGs = True


if needUploadGs :
    # making URL for updating IP to global server
    if not localip_inet:
        # No internet connection, cannot update global server
        logMessages('No internet connection, cannot update global server')
        quit()
    #
    logMessages( "Updating IP address to global server" )
    #
    url_update = '?ip=' + new_ext_ip + '&scuteid=' + scute_id + '&key=' + key + '&port=' + scute_port + '&localip=' + localip_inet
    url_update = gs_url + url_update
    res = urllib2.urlopen( url_update )
    str = res.read()
    logMessages( str )
    res_data = json.loads( str )
    #
    # verify updating result
    if res_data['result'] == "true" :
        cmd = '/bin/touch ' + uploadGsGood
        os.system( cmd )
        logMessages( 'Updating IP to global server successfully' )
    else :
        cmd = '/bin/rm -rf ' + uploadGsGood
        os.system( cmd )
        # os.remove(old_global_ip_file)
        logMessages('Failed to update IP to global server, ' + res_data['status'])
