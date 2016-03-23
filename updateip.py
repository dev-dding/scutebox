#!/usr/bin/env python  
# -*- coding:UTF-8 -*-  

import os
import urllib2
import logging
import logging.handlers
import subprocess
import json

newip = "ipaddr.txt"
oldip = "ipaddr.old"
gs_url = "https://64.140.118.221:3443/updatescuteip.php"
id = "scuteid_001"
key = "scutekey_001"

def GetScuteConfigData():
    p = subprocess.Popen(["php getscuteconfig.php"], shell=True, stdout=subprocess.PIPE)
    ret = p.stdout.read()
    return ret

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
handler = logging.handlers.SysLogHandler(address = '/dev/log')
formatter = logging.Formatter('%(module)s: %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)

# get the router internet ip address by running wget command
os.system('wget -qO- http://ipecho.net/plain > ipaddr.txt')

# update ip to global server when ip changes
if not os.path.isfile(oldip) :
    log.info('Previous IP file not existing')
    # print "Previous IP file not existing"
    os.system("touch %s" % oldip)

try :
    f_old = open(oldip,'r')
    f_new = open(newip,'r')
    newline = f_new.readline()
    oldline = f_old.readline()
    f_old.close()
    f_new.close()
    newline = newline.strip('\n')              # remove the line end
    newline = newline.strip('\r')
    oldline = oldline.strip('\n')              # remove the line end
    oldline = oldline.strip('\r')

except :
	log.critical('File open error for oldip or newip')
    # print "File open error for oldip or newip"

if newline != oldline :
    url_update = gs_url + '?scuteip=' + newline + '&scuteid=' + id + '&key=' + key
    res = urllib2.urlopen( url_update )
    res_data = json.loads( res.read() )
    # print "res :" + res.read()
    # print "newline :" + newline
    # print "oldline :" + oldline
    if res_data['result'] == "true" :
        print "result: " + res_data['result']
        print "status: " + res_data['status']
        os.remove(oldip)
        os.rename(newip, oldip)
    	log.info( 'updated IP to global server successfully' )
    else :
    	log.error('failed to update IP to global server, ' + res_data['status'])
else :
    # log.info('IP Address no change')
    print "IP Address no change"
    

str = GetScuteConfigData()
print str

