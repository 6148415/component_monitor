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
