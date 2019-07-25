#!/usr/bin/env python
# -*- coding: utf-8 -*-


import urllib, urllib2
import time
import json
import commands
import socket
ts = int(time.time())

hostname = socket.gethostname()
payload = []
cmd = " docker ps -a | awk '{if(NR>1) print $NF}'"

ret = commands.getoutput(cmd)

for docker_name in ret.split():
    cmd = "docker inspect %s --format='{{ .State.Running}}'"%docker_name
    ret = commands.getoutput(cmd)
    if ret == 'true':
        status = 1
    else:
        status = 0
    payload.append({
        "endpoint" : '%s-%s'%(hostname, docker_name),
        "metric": "process.status",
        "timestamp": ts,
        "step": 60,
        "value": status,
        "counterType": "GAUGE",
        "tags": "project=oms"
    })

print json.dumps(payload, sort_keys=True,indent=4)
if payload:
    open_falcon_api = 'http://127.0.0.1:1988/v1/push'
    headers = {'Content-Type': 'application/json'}
    request = urllib2.Request(url=open_falcon_api, headers=headers, data=json.dumps(payload))
    response = urllib2.urlopen(request)
    print response.read()
