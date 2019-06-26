#!/bin/env python
#-*- coding:utf-8 -*-


import urllib,urllib2
import socket
import json
import sys
import os
import commands
from optparse import OptionParser

cur_dir = os.path.dirname(os.path.abspath(__file__))

usage = '--url=xxx'
optParser = OptionParser(usage=usage, version='1.0.0')
optParser.add_option('-a', '--oms-addr', action='store', type="string", dest='oms_addr')
option, args = optParser.parse_args()

oms_addr = option.oms_addr
if not oms_addr:
    print '请指定--oms-addr'
    sys.exit(1)


url = 'http://%s/api/getComponent'%oms_addr
#url = 'http://127.0.0.1/api/getComponent'
paramers = {'hostname':socket.gethostname()}

headers = {}
data = urllib.urlencode(paramers)
req = urllib2.Request(url,data,headers)
response = urllib2.urlopen(req)
result = json.loads(response.read())



if result['code'] == 0:
    service_list = []
    port_list = []
    for i in result['data']:    #把每个组件的端端口，管理用户和密码等信息写入到本地文件
        fname = i['fname']
        fport = str(i['fport'])
        fadmin_user = i['fadmin_user']
        fadmin_password = i['fadmin_password']
        if fname not in service_list:
            cmd = "echo '127.0.0.1,%s,%s,%s' > %s/%smon/list.txt"%(fport, fadmin_user, fadmin_password, cur_dir, fname)
            service_list.append(fname)
        else:
            cmd = "echo '127.0.0.1,%s,%s,%s' >> %s/%smon/list.txt"%(fport, fadmin_user, fadmin_password, cur_dir, fname)
        commands.getoutput(cmd)


        #同时把每个组件的监控加入到定时任务里
        cmd = "echo '* * * * * root (cd %s/%smon && python %s_monitor.py list.txt)' >/etc/cron.d/%s.cron"%(cur_dir, fname, fname, fname)
        print cmd
        commands.getoutput(cmd)
        

        port_list.append(fport)


    port_list = list(set(port_list))
    cmd = "echo '%s' > %s/portmon/list.txt"%('\n'.join(port_list), cur_dir)
    commands.getoutput(cmd)    
    cmd = "echo '* * * * * root (cd %s/portmon && python port_monitor.py list.txt)' >/etc/cron.d/port.cron"%(cur_dir)
    print cmd
    commands.getoutput(cmd)






