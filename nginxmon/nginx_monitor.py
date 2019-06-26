#!/bin/env python
#-*- coding:utf-8 -*-

import os,sys  
import os.path  
from os.path import isfile  
from traceback import format_exc  
import socket  
import time  
import json  
import copy

class Resource():  
    def __init__(self, url):
        self.host = socket.gethostname()
        self.url = url

    def get_ngx_active(self):
        cmd="/usr/bin/curl %s 2>/dev/null| grep 'Active' | awk '{print $NF}'" % self.url
        return os.popen(cmd).read().strip("\n")

    def get_ngx_reading(self):
        cmd="/usr/bin/curl %s 2>/dev/null| grep 'Reading' | awk '{print $2}'" % self.url
        return os.popen(cmd).read().strip("\n")

    def get_ngx_writing(self):
        cmd="/usr/bin/curl %s 2>/dev/null| grep 'Writing' | awk '{print $4}'" % self.url
        return os.popen(cmd).read().strip("\n")

    def get_ngx_waiting(self):
        cmd="/usr/bin/curl %s 2>/dev/null| grep 'Waiting' | awk '{print $6}'" % self.url
        return os.popen(cmd).read().strip("\n")

    def get_ngx_accepts(self):
        cmd="/usr/bin/curl %s 2>/dev/null| awk NR==3 | awk '{print $1}'" % self.url
        return os.popen(cmd).read().strip("\n")

    def get_ngx_handled(self):
        cmd="/usr/bin/curl %s 2>/dev/null| awk NR==3 | awk '{print $2}'" % self.url
        return os.popen(cmd).read().strip("\n")

    def get_ngx_requests(self):
        cmd="/usr/bin/curl %s 2>/dev/null| awk NR==3 | awk '{print $3}'" % self.url
        return os.popen(cmd).read().strip("\n")


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
                t['tags'] = "nginx=80"

                output.append(t)

        return output

    def dump_data(self):
        return json.dumps()

def pull_data(datapoints):  
    import requests
    print json.dumps(datapoints, indent=2)
    r = requests.post(falcon_addr, data=json.dumps(datapoints))
    print r.content

if __name__ == "__main__":  
    falcon_addr="http://127.0.0.1:1988/v1/push"
    ngx_status_url="http://127.0.0.1/monitor/nginx_status"
    d = Resource(ngx_status_url).run()
    if d:
        pull_data(d)
