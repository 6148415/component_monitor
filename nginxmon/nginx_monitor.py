#!/bin/env python
#-*- coding:utf-8 -*-

import os,sys  
import os.path  
from os.path import isfile  
from traceback import format_exc  
import fileinput
import socket  
import time  
import json  
import copy
import urllib,urllib2
import requests
cur_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(cur_dir)
sys.path.append(root_dir)

class Resource():  
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.url = "http://%s:%s/monitor/nginx_status"%(self.host, self.port)
        r = requests.get(self.url, timeout=10) 
        if r.status_code == 200:
            self.response = r.content
        else:
            raise Exception(r.content)
        


    def get_ngx_active(self):
        data = self.response.strip().split('\n')
        return data[0].split(':')[1].strip()

    def get_ngx_reading(self):
        data = self.response.strip().split('\n')
        data = data[3]    #'Reading: 0 Writing: 1 Waiting: 0'
        data = data.split() #['Reading:', '0', 'Writing:', '1', 'Waiting:', '0']
        return data[1]

    def get_ngx_writing(self):
        data = self.response.strip().split('\n')
        data = data[3]    #'Reading: 0 Writing: 1 Waiting: 0'
        data = data.split() #['Reading:', '0', 'Writing:', '1', 'Waiting:', '0']
        return data[3]

    def get_ngx_waiting(self):
        data = self.response.strip().split('\n')
        data = data[3]    #'Reading: 0 Writing: 1 Waiting: 0'
        data = data.split() #['Reading:', '0', 'Writing:', '1', 'Waiting:', '0']
        return data[5]

    def get_ngx_accepts(self):
        data = self.response.strip().split('\n')
        data = data[2]    #' 61 61 60 '
        data = data.split()  #['61', '61', '60']
        return data[0]  

    def get_ngx_handled(self):
        data = self.response.strip().split('\n')
        data = data[2]    #' 61 61 60 '
        data = data.split()  #['61', '61', '60']
        return data[1]

    def get_ngx_requests(self):

        data = self.response.strip().split('\n')
        data = data[2]    #' 61 61 60 '
        data = data.split()  #['61', '61', '60']
        return data[2]

    def run(self):
        self.resources_d={
            'nginx.status.active':[self.get_ngx_active,'GAUGE'],
            'nginx.status.reading':[self.get_ngx_reading,'GAUGE'],
            'nginx.status.requests':[self.get_ngx_requests,'GAUGE'],
            'nginx.status.handled':[self.get_ngx_handled,'GAUGE'],
            'nginx.status.accepts':[self.get_ngx_accepts,'GAUGE'],
            'nginx.status.waiting':[self.get_ngx_waiting,'GAUGE'],
            'nginx.status.writing':[self.get_ngx_writing,'GAUGE'],
        }

        output = []
        for resource in  self.resources_d.keys():
                t = {}
                t['endpoint'] = self.host
                t['timestamp'] = int(time.time())
                t['step'] = 60
                t['counterType'] = self.resources_d[resource][1]
                t['metric'] = resource
                t['value']= self.resources_d[resource][0]()
                t['tags'] = "nginxport=80"

                output.append(t)

        return output

    def dump_data(self):
        return json.dumps()

def pull_data(datapoints):  
    print json.dumps(datapoints, indent=2)
    headers = {'Content-Type': 'application/json'}
    request = urllib2.Request(url=falcon_addr, headers=headers, data=json.dumps(datapoints))
    response = urllib2.urlopen(request, timeout=5)
    print response.read()

if __name__ == "__main__":  
    falcon_addr="http://127.0.0.1:1988/v1/push"
    db_list= []
    for line in fileinput.input():
        db_list.append(line.strip())
    for db_info in db_list:
#        host,port,password,endpoint,metric = db_info.split(',')
        host,port,_,_ = db_info.split(',')
        ngx_status_url="http://127.0.0.1/monitor/nginx_status"
        d = Resource(host, port).run()
        if d:
            pull_data(d)
