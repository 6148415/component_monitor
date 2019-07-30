#!/bin/env python
#-*- coding:utf-8 -*-

import json
import time
import fileinput
import datetime
import urllib,urllib2
import socket



open_falcon_api = 'http://127.0.0.1:1988/v1/push'
endpoint = socket.gethostname()
print endpoint
step = 60
ts = int(time.time())

for line in fileinput.input():
    host,port,_,_ = line.strip().split(',')
    tag = 'elasticsearch=%s'%port
    print "http://%s:%s/_cluster/stats?pretty"%(host, port) 
    request = urllib2.Request("http://%s:%s/_cluster/stats?pretty"%(host, port))
    result = urllib2.urlopen(request)
    data = json.loads(result.read())
    p = []
    
    nodes_count_data = data['nodes']['count']['data']
    nodes_count_master = data['nodes']['count']['master']
    nodes_count_total = data['nodes']['count']['total']

    indices_count = data['indices']['count']
    indices_docs_count = data['indices']['docs']['count']
    indices_shards_total = data['indices']['shards']['total']
    primaries_shards_total = data['indices']['shards']['primaries']
  
    mem_used_percent = data['nodes']['os']['mem']['used_percent']

    fs_free = data['nodes']['fs']['free_in_bytes']
    fs_total = data['nodes']['fs']['total_in_bytes']
    fs_used = fs_total - fs_free
    fs_used_percent = '%.2f'%(float(fs_used)/fs_total)

    nodes_cpu_percent = data['nodes']['process']['cpu']['percent']
    
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'es.nodes.count.data','tags':tag, 'value':nodes_count_data}) 
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'es.nodes.count.master','tags':tag, 'value':nodes_count_master}) 
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'es.nodes.count.total','tags':tag, 'value':nodes_count_total}) 

    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'es.indices.count','tags':tag, 'value':indices_count})  
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'es.docs.count','tags':tag, 'value':indices_docs_count}) 
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'es.shards.total','tags':tag, 'value':indices_shards_total})
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'es.shards.primaries','tags':tag, 'value':primaries_shards_total})

    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'es.mem.used.percent','tags':tag, 'value':mem_used_percent})   
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'es.fs.used.percent','tags':tag, 'value':fs_used_percent}) 
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'es.nodes.cpu.percent','tags':tag, 'value':nodes_cpu_percent})  
    print json.dumps(p, indent=4)


    headers = {'Content-Type': 'application/json'}
    request = urllib2.Request(url=open_falcon_api, headers=headers, data=json.dumps(p))
    response = urllib2.urlopen(request, timeout=5)
    print response.read()

