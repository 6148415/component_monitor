#!/bin/env python
#-*- coding:utf-8 -*-


import urllib,urllib2
import socket
import json
import sys
import os
import commands

cur_dir = os.path.dirname(os.path.abspath(__file__))

url = 'http://127.0.0.1/api/getComponent'
paramers = {'hostname':socket.gethostname()}

headers = {}
data = urllib.urlencode(paramers)
req = urllib2.Request(url,data,headers)
response = urllib2.urlopen(req)
result = json.loads(response.read())


print result


if result['code'] == 0:
    services = []
    for i in result['data']:    #把每个组件的端端口，管理用户和密码等信息写入到本地文件
        fname = i['fname']
        fport = i['fport']
        fadmin_user = i['fadmin_user']
        fadmin_password = i['fadmin_password']
        if fname not in services:
            cmd = "echo '127.0.0.1,%s,%s,%s' > %s/%smon/list.txt"%(fport, fadmin_user, fadmin_password, cur_dir, fname)
            services.append(fname)
        else:
            cmd = "echo '127.0.0.1,%s,%s,%s' >> %s/%smon/list.txt"%(fport, fadmin_user, fadmin_password, cur_dir, fname)
        commands.getoutput(cmd)


        #同时把每个组件的监控加入到定时任务里
        cmd = "echo '* * * * * root (cd %s/%smon && python %s_monitor.py list.txt' >/etc/cron.d/%s.cron"%(cur_dir, fname, fname, fname)
        commands.getoutput(cmd)
        


