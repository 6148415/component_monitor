#!/bin/env python
# -*- encoding: utf-8 -*-

import socket
import  time
import urllib, urllib2
import commands
import json

endpoint = socket.gethostname()

with open('list.txt', 'r') as f:
    content = f.read().strip()



if content:
    port_list = content.split()

    ts = int(time.time())
    payload = []

    for port in port_list:
        cmd = "netstat  -an |grep :%s |grep LIST |wc -l"%(port)
        result = commands.getoutput(cmd)
        if int(result) >= 0:
            value = 1
        else:
            value = 0

        
        payload.append({
            "endpoint": endpoint,
            "metric": 'listen.port',
            "timestamp": ts,
            "step": 60,
            "value": value,
            "counterType": "GAUGE",
            "tags": "port=%s,project=oms"%port
        })

    request_url = 'http://127.0.0.1:1988/v1/push'
    headers = {'Content-Type': 'application/json'}
    request = urllib2.Request(url=request_url, headers=headers, data=json.dumps(payload))
    response = urllib2.urlopen(request)
    print json.dumps(payload, indent=2)
    print response.read()
