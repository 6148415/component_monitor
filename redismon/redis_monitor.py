#!/bin/env python
#-*- coding:utf-8 -*-

import json
import time
import re
import redis
import requests
import fileinput
import datetime
import socket

class RedisMonitorInfo():

    def __init__(self,host,port,password):
        self.host     = host
        self.port     = port
        self.password = password

    def stat_info(self):
         try:
            r = redis.Redis(host=self.host, port=self.port, password=self.password)
            stat_info = r.info()
            return stat_info
         except Exception, e:
            print (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
            print e
            return dict()

    def cmdstat_info(self):
        try:
            r = redis.Redis(host=self.host, port=self.port, password=self.password)
            cmdstat_info = r.info('Commandstats')
            return cmdstat_info
        except Exception, e:
            print (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
            print e
            return dict()

if __name__ == '__main__':

    open_falcon_api = 'http://127.0.0.1:1988/v1/push'

    db_list= []
    for line in fileinput.input():
        db_list.append(line.strip())
    for db_info in db_list:
#        host,port,password,endpoint,metric = db_info.split(',')
        host,port,password = db_info.split(',')
        endpoint = socket.gethostname()
        timestamp = int(time.time())
        step      = 60
        falcon_type = 'COUNTER'
#        tags      = "port=%s" %port
        tags      = "redis=%s"%port
    
        conn = RedisMonitorInfo(host,port,password)
    
        #查看各个命令每秒执行次数
        redis_cmdstat_dict = {}
        redis_cmdstat_list = []
        cmdstat_info = conn.cmdstat_info()
        for cmdkey in cmdstat_info:
            redis_cmdstat_dict[cmdkey] = cmdstat_info[cmdkey]['calls']
        for _key,_value in redis_cmdstat_dict.items():
            falcon_format = {
                    'Metric': '%s' % (_key),
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
                    'Metric': '%s' % (_key),
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
        requests.post(open_falcon_api, data=json.dumps(load_data))
