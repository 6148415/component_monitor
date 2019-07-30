#!/bin/env python
# -*- encoding: utf-8 -*-

from __future__ import division
import MySQLdb
import datetime
import time
import os
import sys
import fileinput
import urllib,urllib2
import json
import re
import socket


class MySQLMonitorInfo():

    def __init__(self,host,port,user,password):
        self.host     = host
        self.port     = port
        self.user     = user
        self.password = password

    def stat_info(self):
        try:
            m = MySQLdb.connect(host=self.host,user=self.user,passwd=self.password,port=self.port,charset='utf8')
            query = "SHOW GLOBAL STATUS"
            cursor = m.cursor()
            cursor.execute(query)
            Str_string = cursor.fetchall()
            Status_dict = {}
            for Str_key,Str_value in Str_string:
                Status_dict[Str_key] = Str_value
            cursor.close()
            m.close()
            return Status_dict

        except Exception, e:
            print (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
            print e
            Status_dict = {}
            return Status_dict 

    def engine_info(self):
        try:
            m = MySQLdb.connect(host=self.host,user=self.user,passwd=self.password,port=self.port,charset='utf8')
            _engine_regex = re.compile(ur'(History list length) ([0-9]+\.?[0-9]*)\n')
            query = "SHOW ENGINE INNODB STATUS"
            cursor = m.cursor()
            cursor.execute(query)
            Str_string = cursor.fetchone()
            a,b,c = Str_string
            cursor.close()
            m.close()
            return dict(_engine_regex.findall(c))
        except Exception, e:
            print (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
            print e
            return dict(History_list_length=0)

if __name__ == '__main__':

    open_falcon_api = 'http://127.0.0.1:1988/v1/push'
    db_list= []
    for line in fileinput.input():
        db_list.append(line.strip())
    for db_info in db_list:
#        host,port,user,password,endpoint,metric = db_info.split(',')
        host,port,user,password = db_info.split(',')
        endpoint = socket.gethostname()
        timestamp = int(time.time())
        step      = 60
#        tags      = "port=%s" %port
        tags      = "mysql=%s"%port
        conn = MySQLMonitorInfo(host,int(port),user,password)
        stat_info = conn.stat_info()
        engine_info = conn.engine_info()

        mysql_stat_list = []
        monitor_keys = [
            ('Com_select','COUNTER'),
            ('Qcache_hits','COUNTER'),
            ('Com_insert','COUNTER'),
            ('Com_update','COUNTER'),
            ('Com_delete','COUNTER'),
            ('Com_replace','COUNTER'),
            ('MySQL_QPS','COUNTER'),
            ('MySQL_TPS','COUNTER'),
            ('ReadWrite_ratio','GAUGE'),
            ('Innodb_buffer_pool_read_requests','COUNTER'),
            ('Innodb_buffer_pool_reads','COUNTER'),
            ('Innodb_buffer_read_hit_ratio','GAUGE'),
            ('Innodb_buffer_pool_pages_flushed','COUNTER'),
            ('Innodb_buffer_pool_pages_free','GAUGE'),
            ('Innodb_buffer_pool_pages_dirty','GAUGE'),
            ('Innodb_buffer_pool_pages_data','GAUGE'),
            ('MySQL_bytes_received','COUNTER'),
            ('MySQL_bytes_sent','COUNTER'),
            ('Innodb_rows_deleted','COUNTER'),
            ('Innodb_rows_inserted','COUNTER'),
            ('Innodb_rows_read','COUNTER'),
            ('Innodb_rows_updated','COUNTER'),
            ('Innodb_os_log_fsyncs','COUNTER'),
            ('Innodb_os_log_written','COUNTER'),
            ('Created_tmp_disk_tables','COUNTER'),
            ('Created_tmp_tables','COUNTER'),
            ('MySQL.Connections','COUNTER'),
            ('Innodb_log_waits','COUNTER'),
            ('Slow_queries','COUNTER'),
            ('Binlog_cache_disk_use','COUNTER')
        ]

        for _key,falcon_type in monitor_keys:
            if _key == 'MySQL_QPS':
                _value = int(stat_info.get('Com_select',0)) + int(stat_info.get('Qcache_hits',0))
            elif _key == 'MySQL_TPS':
                _value = int(stat_info.get('Com_insert',0)) + int(stat_info.get('Com_update',0)) + int(stat_info.get('Com_delete',0)) + int(stat_info.get('Com_replace',0))
            elif _key == 'Innodb_buffer_read_hit_ratio':
                try:
                    _value = round((int(stat_info.get('Innodb_buffer_pool_read_requests',0)) - int(stat_info.get('Innodb_buffer_pool_reads',0)))/int(stat_info.get('Innodb_buffer_pool_read_requests',0)) * 100,3)
                except ZeroDivisionError:
                    _value = 0
            elif _key == 'ReadWrite_ratio':
                try:
                    _value = round((int(stat_info.get('Com_select',0)) + int(stat_info.get('Qcache_hits',0)))/(int(stat_info.get('Com_insert',0)) + int(stat_info.get('Com_update',0)) + int(stat_info.get('Com_delete',0)) + int(stat_info.get('Com_replace',0))),2)
                except ZeroDivisionError:
                    _value = 0            
            else:
                _value = int(stat_info.get(_key,0))

            falcon_format = {
                    'Metric': '%s' % (_key.replace('_', '.')),
                    'Endpoint': endpoint,
                    'Timestamp': timestamp,
                    'Step': step,
                    'Value': _value,
                    'CounterType': falcon_type,
                    'TAGS': tags
                }
            mysql_stat_list.append(falcon_format)

        #_key : History list length
        for _key,_value in  engine_info.items():
            _key = "Undo_Log_Length"
            falcon_format = {
                    'Metric': '%s' % (_key.replace('_', '.')),
                    'Endpoint': endpoint,
                    'Timestamp': timestamp,
                    'Step': step,
                    'Value': int(_value),
                    'CounterType': "GAUGE",
                    'TAGS': tags
                }
            mysql_stat_list.append(falcon_format)

        print json.dumps(mysql_stat_list,sort_keys=True,indent=4)
        headers = {'Content-Type': 'application/json'}
        request = urllib2.Request(url=open_falcon_api, headers=headers, data=json.dumps(mysql_stat_list))
        response = urllib2.urlopen(request, timeout=5)
        print response.read()
