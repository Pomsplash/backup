#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
---------------------------------------------------------------------
file   : check_storage.py
author : Pom
date   : 2019.06.06
---------------------------------------------------------------------
"""
import itertools
import logging
import logging.config
import os
import re
import subprocess
import syslog
import time
import datetime

PREV_INFO_FILE_PATH = "/tmp/memory.txt"
UNIX_TIME = int(time.time())


def main():
    curr_memory = get_current_memory()
    pre_memory = get_previous_memory()
    save_current_memory(curr_memory)
    check_memory(curr_memory,pre_memory)


def get_current_memory():
    curr_memory = {}
    cmd = "top -n 1"
    ret = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).communicate()[0]
    lines = ret.split("\n")
    curr_memory = lines[3]
    curr_memory = str(UNIX_TIME) + " " + curr_memory
    return curr_memory

def get_previous_memory():
    pre_memory = {}
    if os.path.isfile(PREV_INFO_FILE_PATH):
        fp = open(PREV_INFO_FILE_PATH, "r")
        pre_memory = fp.read()
        
    return pre_memory

def check_memory(curr_memory,pre_memory):

    curr_memory_word = curr_memory.split()
    pre_memory_word = pre_memory.split()

    curr_memory_word[7] = int(filter(str.isdigit, curr_memory_word[7]))
    pre_memory_word[7] = int(filter(str.isdigit, pre_memory_word[7]))
    # m = y2-y1 /x2-x1

    diff_time = int(curr_memory_word[0]) - int(pre_memory_word[0])
    diff_memory = int(curr_memory_word[7]) - int(pre_memory_word[7])
    print "Different time :", diff_time
    print "Different memory :", abs(diff_memory)
    slope = float(diff_memory)/float(diff_time)
    print "Slope :", abs(slope)
    

def save_current_memory(curr_memory):
    fp = open(PREV_INFO_FILE_PATH, "w")
    fp.write(curr_memory)
    fp.close()

if __name__ == '__main__':
    main()
