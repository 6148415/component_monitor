#!/bin/env python
#-*- coding:utf-8 -*-


import urllib,urllib2
import socket
import json
import sys
import os
import commands
from optparse import OptionParser
import cPickle as p

cur_dir = os.path.dirname(os.path.abspath(__file__))
from common import get_local_ip

usage = '--url=xxx'
optParser = OptionParser(usage=usage, version='1.0.0')
optParser.add_option('-a', '--oms-addr', action='store', type="string", dest='oms_addr')
option, args = optParser.parse_args()

oms_addr = option.oms_addr
if not oms_addr:
    print '请指定--oms-addr'
    sys.exit(1)


url = 'http://%s/api/getComponent'%oms_addr

headers = {}
paramers = {}
data = urllib.urlencode(paramers)
req = urllib2.Request(url,data,headers)
response = urllib2.urlopen(req)
result = json.loads(response.read())


if result['code'] == 0:
    service_list = []
    jmx_info = {}
    #先清除/etc/corn.d目录下所有的cron文件
    cmd = 'cd /etc/cron.d && find . -name "*.cron" |grep -v "ntp.cron" |grep -v "docker.cron" |xargs -i rm -rf {}'
    commands.getoutput(cmd)
    #清空端口列表文件
    cmd = 'cd %s/portmon && rm -rf list.txt'%cur_dir
    commands.getoutput(cmd)

    for i in result['data']:    #把每个组件的端端口，管理用户和密码等信息写入到本地文件
        fhost = i['fhost']
        fname = i['fname']
        fport = str(i['fport'])
        fadmin_user = i['fadmin_user']
        fadmin_password = i['fadmin_password']

        #收集ip和端口，用来统一监控端口状态
        cmd = "echo '%s,%s' >> %s/portmon/list.txt"%(fhost, fport, cur_dir)
        commands.getoutput(cmd)

        if fname == 'jmx':
            if jmx_info.has_key(fhost):
                jmx_info[fhost].append(fport)
            else:
                jmx_info[fhost] = [fport]
            continue

        if fname not in service_list:
            cmd = "echo '%s,%s,%s,%s' > %s/%smon/list.txt"%(fhost, fport, fadmin_user, fadmin_password, cur_dir, fname)
            service_list.append(fname)
        else:
            cmd = "echo '%s,%s,%s,%s' >> %s/%smon/list.txt"%(fhost, fport, fadmin_user, fadmin_password, cur_dir, fname)
        commands.getoutput(cmd)


        #同时把每个组件的监控加入到定时任务里
        cmd = "echo '* * * * * root (cd %s/%smon && python %s_monitor.py list.txt)' >/etc/cron.d/%s.cron"%(cur_dir, fname, fname, fname)
        print cmd
        commands.getoutput(cmd)
        


    cmd = "echo '* * * * * root (cd %s/portmon && python port_monitor.py list.txt)' >/etc/cron.d/port.cron"%(cur_dir)
    print cmd
    commands.getoutput(cmd)



    
    for jmx_host, port_list in jmx_info.items():
        port_list = list(set(port_list))
        

        cmd = 'cd {0}/jmxmon && cp -rf conf.example.properties conf.properties.{1} && \
            sed -i "s/jmx.ports=/jmx.ports={2}/g" conf.properties.{1} && \
            sed -i "s/hostname=/hostname={1}/g" conf.properties.{1}'.format(cur_dir, jmx_host, ','.join(port_list))
        commands.getoutput(cmd)

        cmd = "echo '* * * * * root (cd {0}/jmxmon && export jmx_host={1} && \
            timeout 10 java -cp ./jmxmon-0.0.2-jar-with-dependencies.jar com.stephan.tof.jmxmon.JMXMonitor  conf.properties.{1})' \
            >> /etc/cron.d/jmx.cron".format(cur_dir, jmx_host)

        commands.getoutput(cmd)





