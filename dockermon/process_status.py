#!/usr/bin/env python
# -*- coding: utf-8 -*-

#上报进程状态的同时，还需要将容器信息写入到oms

import urllib, urllib2
import time
import json
import commands
import socket
import cPickle as p
import os
import sys
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

ts = int(time.time())

hostname = socket.gethostname()
payload = []

f = file('%s/containers.pkl'%cur_dir)
containers = p.load(f)
f.close() 

cmd = " docker ps -a | awk '{if(NR>1) print $NF}'"

ret = commands.getoutput(cmd)
container_list = ret.split()
for docker_name in container_list:
    cmd = "docker inspect %s --format='{{ .State.Running}}'"%docker_name
    ret = commands.getoutput(cmd)
    if ret == 'true':
        status = 1
    else:
        status = 0
    payload.append({
        "endpoint" : '%s/%s'%(hostname, docker_name),
        "metric": "process.status",
        "timestamp": ts,
        "step": 60,
        "value": status,
        "counterType": "GAUGE",
        "tags": "project=oms"
    })

    cmd = "docker inspect --format '{{ .NetworkSettings.IPAddress }}' %s"%docker_name
    ip = commands.getoutput(cmd)

    if hostname in containers and docker_name in containers[hostname]:
        pass
    else:   #上报容器
        paramers = {'fhostname':docker_name, 'fmaster':hostname, 'fip': ip} 
        data = urllib.urlencode(paramers)
        req = urllib2.Request('http://%s/api/container/add'%oms_addr, data)
        response = urllib2.urlopen(req)
        result = json.loads(response.read())        
        if result['code'] == 0:     #刷新缓存
            if hostname not in containers:
                containers[hostname] = [docker_name]
            else:
                containers[hostname].append(docker_name)
            f = file('%s/containers.pkl'%cur_dir, 'w')
            p.dump(containers, f)
            f.close()

        
        



print json.dumps(payload, sort_keys=True,indent=4)
if payload:
    open_falcon_api = 'http://127.0.0.1:1988/v1/push'
    headers = {'Content-Type': 'application/json'}
    request = urllib2.Request(url=open_falcon_api, headers=headers, data=json.dumps(payload))
    response = urllib2.urlopen(request, timeout=5)
    print response.read()

        
