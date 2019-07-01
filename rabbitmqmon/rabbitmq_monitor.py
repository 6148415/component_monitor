#!/bin/env python
#-*- coding:utf-8 -*-

__author__ = 'iambocai'

import sys, urllib2, base64, json, time,socket
import fileinput


rbq_list= []
for line in fileinput.input():
    rbq_list.append(line.strip())
for rbq_info in rbq_list:
    host,port,username,password = rbq_info.split(',')
    endpoint = socket.gethostname()

    step = 60
    ts = int(time.time())
    keys = ('messages_ready', 'messages_unacknowledged')
    rates = ('ack', 'deliver', 'deliver_get', 'publish')

    request = urllib2.Request("http://127.0.0.1:15672/api/queues")
    # see #issue4
    base64string = base64.b64encode('admin:admin')
    request.add_header("Authorization", "Basic %s" % base64string)   
    result = urllib2.urlopen(request)
    data = json.loads(result.read())
    tag = 'rabbitmq=%s'%port
    #tag = sys.argv[1].replace('_',',').replace('.','=')

    p = []
    for queue in data:
        # ready and unack
        msg_total = 0
        for key in keys:
            q = {}
            q["endpoint"] = endpoint
            q['timestamp'] = ts
            q['step'] = step
            q['counterType'] = "GAUGE"
            q['metric'] = 'rabbitmq.%s' % key
            q['tags'] = 'name=%s,%s' % (queue['name'],tag)
            q['value'] = int(queue[key])
            msg_total += q['value']
            p.append(q)

        # total
        q = {}
        q["endpoint"] = endpoint
        q['timestamp'] = ts
        q['step'] = step
        q['counterType'] = "GAUGE"
        q['metric'] = 'rabbitmq.messages_total'
        q['tags'] = 'name=%s,%s' % (queue['name'],tag)
        q['value'] = msg_total
        p.append(q)
        
        # rates
        for rate in rates:
            q = {}
            q["endpoint"] = endpoint
            q['timestamp'] = ts
            q['step'] = step
            q['counterType'] = "GAUGE"
            q['metric'] = 'rabbitmq.%s_rate' % rate
            q['tags'] = 'name=%s,%s' % (queue['name'],tag)
            try:
                q['value'] = int(queue['message_stats']["%s_details" % rate]['rate'])
            except:
                q['value'] = 0
            p.append(q)



    request = urllib2.Request("http://127.0.0.1:15672/api/nodes")	
    request.add_header("Authorization", "Basic %s" % base64string)
    result = urllib2.urlopen(request)
    data = json.loads(result.read())	

    mem_used = data[0]['mem_used']
    mem_limit = data[0]['mem_limit']    
    mem_used_rate = '%.2f'%(float(mem_used)/mem_limit*100)
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.mem_used_rate','tags':tag, 'value':mem_used_rate})

    proc_used = data[0]['proc_used']
    proc_total = data[0]['proc_total']
    proc_used_rate = '%.2f'%(float(proc_used)/proc_total*100)
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.proc_used_rate','tags':tag, 'value':proc_used_rate})


    request = urllib2.Request("http://127.0.0.1:15672/api/overview")
    request.add_header("Authorization", "Basic %s" % base64string)
    result = urllib2.urlopen(request)
    data = json.loads(result.read())

    messages_total = data['queue_totals']['messages']
    messages_ready = data['queue_totals']['queue_totals']
    messages_unacknowledged = data['queue_totals']['messages_unacknowledged']
    
    channels = data['object_totals']['channels']
    connections = data['object_totals']['connections'] 
    consumers = data['object_totals']['consumers']
    exchanges = data['object_totals']['exchanges']
    queues = data['object_totals']['queues']

    print json.dumps(p, indent=4)





    method = "POST"
    handler = urllib2.HTTPHandler()
    opener = urllib2.build_opener(handler)
    url = 'http://127.0.0.1:1988/v1/push'
    request = urllib2.Request(url, data=json.dumps(p) )
    request.add_header("Content-Type",'application/json')
    request.get_method = lambda: method
    try:
        connection = opener.open(request)
    except urllib2.HTTPError,e:
        connection = e

    # check. Substitute with appropriate HTTP code.
    if connection.code == 200:
        print connection.read()
    else:
        print '{"err":1,"msg":"%s"}' % connection

