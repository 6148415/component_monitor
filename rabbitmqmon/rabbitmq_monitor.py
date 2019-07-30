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

    # see #issue4
    base64string = base64.b64encode('%s:%s'%(username, password))
    tag = 'rabbitmq=%s'%port
    #tag = sys.argv[1].replace('_',',').replace('.','=')

    p = []


    request = urllib2.Request("http://127.0.0.1:15672/api/nodes")	
    request.add_header("Authorization", "Basic %s" % base64string)
    result = urllib2.urlopen(request)
    data = json.loads(result.read())	

    mem_used = data[0]['mem_used']
    mem_limit = data[0]['mem_limit']    
    mem_used_rate = '%.2f'%(float(mem_used)/mem_limit*100)
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.mem.used','tags':tag, 'value':mem_used})
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.mem.used.percent','tags':tag, 'value':mem_used_rate})

    proc_used = data[0]['proc_used']
    proc_total = data[0]['proc_total']
    proc_used_rate = '%.2f'%(float(proc_used)/proc_total*100)
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.proc.used.percent','tags':tag, 'value':proc_used_rate})


    request = urllib2.Request("http://127.0.0.1:15672/api/overview")
    request.add_header("Authorization", "Basic %s" % base64string)
    result = urllib2.urlopen(request)
    data = json.loads(result.read())


    messages_total = data['queue_totals']['messages']
    messages_ready = data['queue_totals']['messages_ready']
    messages_unacknowledged = data['queue_totals']['messages_unacknowledged']
    
    channels = data['object_totals']['channels']
    connections = data['object_totals']['connections'] 
    consumers = data['object_totals']['consumers']
    exchanges = data['object_totals']['exchanges']
    queues = data['object_totals']['queues']

    ack_rate = data['message_stats']['ack_details']['rate']
    deliver_rate = data['message_stats']['deliver_details']['rate']
    deliver_get_rate = data['message_stats']['deliver_get_details']['rate']
    deliver_no_ack_rate = data['message_stats']['deliver_no_ack_details']['rate']
    get_rate = data['message_stats']['get_details']['rate']
    get_no_ack_rate = data['message_stats']['get_no_ack_details']['rate']
    publish_rate = data['message_stats']['publish_details']['rate']
    redeliver_rate = data['message_stats']['redeliver_details']['rate']



    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.messages.total','tags':tag, 'value':messages_total})
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.messages.ready','tags':tag, 'value':messages_ready})
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.messages.unacknowledged','tags':tag, 'value':messages_unacknowledged})
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.channels','tags':tag, 'value':channels})
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.connections','tags':tag, 'value':connections})
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.consumers','tags':tag, 'value':consumers})
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.exchanges','tags':tag, 'value':exchanges})
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.queues','tags':tag, 'value':queues})

    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.ack.rate','tags':tag, 'value':ack_rate})
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.deliver.rate','tags':tag, 'value':deliver_rate})
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.deliver_get.rate','tags':tag, 'value':deliver_get_rate})
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.deliver_no_ack.rate','tags':tag, 'value':deliver_no_ack_rate})
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.get.rate','tags':tag, 'value':get_rate})
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.get_no_ack.rate','tags':tag, 'value':get_no_ack_rate})
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.publish.rate','tags':tag, 'value':publish_rate})
    p.append({'endpoint':endpoint, 'timestamp':ts, 'step':step, 'counterType':'GAUGE', 'metric':'rabbitmq.redeliver.rate','tags':tag, 'value':redeliver_rate})

    print json.dumps(p, indent=4)


    method = "POST"
    handler = urllib2.HTTPHandler()
    opener = urllib2.build_opener(handler)
    url = 'http://127.0.0.1:1988/v1/push'
    request = urllib2.Request(url, data=json.dumps(p) )
    request.add_header("Content-Type",'application/json')
    request.get_method = lambda: method
    try:
        connection = opener.open(request, timeout=5)
    except urllib2.HTTPError,e:
        connection = e

    # check. Substitute with appropriate HTTP code.
    if connection.code == 200:
        print connection.read()
    else:
        print '{"err":1,"msg":"%s"}' % connection

