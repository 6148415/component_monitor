#!/bin/env python
#-*- coding:utf-8 -*-

import socket
import sys


def get_local_ip():

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    return s.getsockname()[0]


