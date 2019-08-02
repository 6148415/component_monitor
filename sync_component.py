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
    jmxport_list = []       #jmx端口需要特殊处理
    #先清除/etc/corn.d目录下所有的cron文件
    cmd = 'cd /etc/cron.d && find . -name "*.cron" |grep -v "ntp.cron" |xrags -i rm -rf {}'

    commands.getoutput(cmd)
    for i in result['data']:    #把每个组件的端端口，管理用户和密码等信息写入到本地文件
        fname = i['fname']
        fport = str(i['fport'])
        fadmin_user = i['fadmin_user']
        fadmin_password = i['fadmin_password']

        if fname == 'jmx':
            jmxport_list.append(fport)

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


    if port_list:
        port_list = list(set(port_list))
        cmd = "echo '%s' > %s/portmon/list.txt"%('\n'.join(port_list), cur_dir)
        commands.getoutput(cmd)    
        cmd = "echo '* * * * * root (cd %s/portmon && python port_monitor.py list.txt)' >/etc/cron.d/port.cron"%(cur_dir)
        print cmd
        commands.getoutput(cmd)



    if jmxport_list:
        jmxport_list = list(set(jmxport_list))
        cmd = 'cd %s/jmxmon && cp -rf conf.example.properties conf.properties && sed -i "s/jmx.ports=/jmx.ports=%s/g" conf.properties && ./control restart'%(
            cur_dir, ','.join(jmxport_list)
        )
        print cmd
        commands.getoutput(cmd)
        


    #安装python组件
    if 'msyql' in service_list:
        cmd = 'yum install python-devel -y;yum install mysql-devel -y;\
            pip install MySQL-python -i  http://pypi.doubanio.com/simple --trusted-host pypi.doubanio.com'
        os.system(cmd)




#########部署cadvisor#############
#cadvisor一旦部署后会自动发现本机的docker服

cmd = "docker"
result = commands.getstatusoutput(cmd)
if result[0] != 0:
    sys.exit(1)


cmd = "netstat  -an |grep :%s |grep LIST |wc -l"%(18080)
result = commands.getoutput(cmd)
if int(result) ==  0:
    cmd = 'cd %s/dockermon && ./cadvisor -port=%s &'%(cur_dir, 18080)
    os.system(cmd)

url = 'http://%s/api/container/list'%oms_addr


paramers = {}

headers = {}
data = urllib.urlencode(paramers)
req = urllib2.Request(url,data,headers)
response = urllib2.urlopen(req)
result = json.loads(response.read())

if result['code'] == 0:    #将容器列表缓存到本地文件
    f = file('%s/dockermon/containers.pkl'%cur_dir, 'w')
    p.dump(result['data'], f)
    f.close()
    
else:
    print '初始化缓存容器列表失败: %s'%result['mesage']
    sys.exit(1)
    

cmd = "echo '* * * * * root (cd %s/dockermon && python process_status.py --oms-addr=%s)' >/etc/cron.d/docker.cron"%(cur_dir, oms_addr)
print cmd
commands.getoutput(cmd)
cmd = "echo '* * * * * root (cd %s/dockermon && ./uploadCadvisorData)' >>/etc/cron.d/docker.cron"%(cur_dir)
print cmd
commands.getoutput(cmd)
