#!/bin/env python
#-*- coding:utf-8 -*-

import json
import time
import re
import redis
import fileinput
import datetime
import socket
import urllib,urllib2
import os
import sys
cur_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(cur_dir)
sys.path.append(root_dir)

class RedisMonitorInfo():

    def __init__(self,host,port,password):
        self.host     = host
        self.port     = port
        self.password = password

    def stat_info(self):
        try:
            r = redis.Redis(host=self.host, port=self.port, password=self.password)
            stat_info = r.info()
        except Exception, e:
            stat_info = {}
        return stat_info  


    def cmdstat_info(self):
        try:
            r = redis.Redis(host=self.host, port=self.port, password=self.password)
            cmdstat_info = r.info('Commandstats')

        except Exception, e:
            cmdstat_info = {}
        return cmdstat_info	


if __name__ == '__main__':

    open_falcon_api = 'http://127.0.0.1:1988/v1/push'

    db_list= []
    for line in fileinput.input():
        db_list.append(line.strip())
    for db_info in db_list:
#        host,port,password,endpoint,metric = db_info.split(',')
        host,port,_,password = db_info.split(',')
        endpoint = host
        timestamp = int(time.time())
        step      = 60
        falcon_type = 'COUNTER'
#        tags      = "port=%s" %port
        tags      = "redisport=%s"%port
    
        conn = RedisMonitorInfo(host,port,password)
    
        #查看各个命令每秒执行次数
        redis_cmdstat_dict = {}
        redis_cmdstat_list = []
        cmdstat_info = conn.cmdstat_info()
        for cmdkey in cmdstat_info:
            print cmdstat_info[cmdkey]
            redis_cmdstat_dict[cmdkey] = cmdstat_info[cmdkey].get('calls', 0)
        for _key,_value in redis_cmdstat_dict.items():
            falcon_format = {
                    'Metric': 'redis.%s' % (_key.replace('_','.')),
                    'Endpoint': endpoint,
                    'Timestamp': timestamp,
                    'Step': step,
                    'Value': int(_value),
                    'CounterType': falcon_type,
                    'TAGS': tags
                }
            redis_cmdstat_list.append(falcon_format)
    
        #查看Redis各种状态,根据需要增删监控项,str的值需要转换成int
        redis_stat_list = []
        monitor_keys = [
            ('connected_clients','GAUGE'),
            ('blocked_clients','GAUGE'),
            ('used_memory','GAUGE'),
            ('used_memory_rss','GAUGE'),
            ('mem_fragmentation_ratio','GAUGE'),
            ('total_commands_processed','COUNTER'),
            ('rejected_connections','COUNTER'),
            ('expired_keys','COUNTER'),
            ('evicted_keys','COUNTER'),
            ('keyspace_hits','COUNTER'),
            ('keyspace_misses','COUNTER'),
            ('keyspace_hit_ratio','GAUGE'),
            ('keys_num','GAUGE'),
        ]
        stat_info = conn.stat_info()   
        for _key,falcon_type in monitor_keys:
            #计算命中率
            if _key == 'keyspace_hit_ratio':
                try:
                    _value = round(float(stat_info.get('keyspace_hits',0))/(int(stat_info.get('keyspace_hits',0)) + int(stat_info.get('keyspace_misses',0))),4)*100
                except ZeroDivisionError:
                    _value = 0
            #碎片率是浮点数
            elif _key == 'mem_fragmentation_ratio':
                _value = float(stat_info.get(_key,0))
            #拿到key的数量
            elif _key == 'keys_num':
                _value = 0 
                for i in range(16):
                    _key = 'db'+str(i)
                    _num = stat_info.get(_key)
                    if _num:
                        _value += int(_num.get('keys'))
                _key = 'keys_num'
            #其他的都采集成counter，int
            else:
                try:
                    _value = int(stat_info[_key])
                except:
                    continue
            falcon_format = {
                    'Metric': 'redis.%s' % (_key.replace('_','.')),
                    'Endpoint': endpoint,
                    'Timestamp': timestamp,
                    'Step': step,
                    'Value': _value,
                    'CounterType': falcon_type,
                    'TAGS': tags
                }
            redis_stat_list.append(falcon_format)
    
        load_data = redis_stat_list+redis_cmdstat_list
        print json.dumps(load_data,sort_keys=True,indent=4)
        headers = {'Content-Type': 'application/json'}
        request = urllib2.Request(url=open_falcon_api, headers=headers, data=json.dumps(load_data))
        response = urllib2.urlopen(request, timeout=5)
        print response.read()
