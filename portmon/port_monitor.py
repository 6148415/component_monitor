#!/bin/env python
# -*- encoding: utf-8 -*-

import socket
import  time
import urllib, urllib2
import fileinput
import commands
import json
import os
import sys
cur_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(cur_dir)
sys.path.append(root_dir)


def check_port(host, port):
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sk.settimeout(1)
    try:
        sk.connect((host, port))
        result = True
    except Exception, e:
        result = False
    return result
    

port_list= []
for line in fileinput.input():
    port_list.append(line.strip())


ts = int(time.time())
payload = []

for port_info in port_list:
    host,port = port_info.split(',')

    result = check_port(host, int(port))
    if result:
        value = 1
    else:
        value = 0

        
    payload.append({
        "endpoint": host,
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
response = urllib2.urlopen(request, timeout=5)
print json.dumps(payload, indent=2)
print response.read()
