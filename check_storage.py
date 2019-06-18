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

PREV_INFO_FILE_PATH = "/tmp/storage.txt"
DIFF_VALUE = 1000  # MB
TOUCH_TMP_FILE_NAME = "check_storage_tmp.dat"
DIFF_DAY = 1 # Days

logging.config.fileConfig('logger.ini', disable_existing_loggers=False)
logger = logging.getLogger('check_storage')

def main():
    # 現在のストレージの状況を取得する
    cur_storage = get_current_storage()

    # 前回のストレージの状況を取得する
    pre_storage = get_previous_storage()

    # ストレージの状況をチェックする
    check_storage(cur_storage, pre_storage)

    # iノードの状況をチェックする
    check_inode(cur_storage)

    # 現在のストレージの状況をファイルに書き込む
    save_storage_info(cur_storage)

def get_current_storage():
    cur_storage = {}
    cmd = "df -m --portability"
    ret = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).communicate()[0]
    lines = ret.split("\n")
    for line in lines:
        cols = line.split()
        if len(cols) < 6:
            continue
        # 容量が数値ではない場合は飛ばす
        if not cols[1].isdigit():
            continue
        # ディクショナリに格納する
        # cols[0]: Filesystem
        # cols[1]: Capacity
        # cols[2]: Used
        # cols[3]: Available
        # cols[4]: Average
        # cols[5]: Mounted
        cur_storage[cols[0]] = (cols[1], cols[2], cols[3], cols[4], cols[5],int(time.time()))
    return cur_storage

def get_previous_storage():
    pre_storage = {}
    if os.path.isfile(PREV_INFO_FILE_PATH):
        fp = open(PREV_INFO_FILE_PATH, "r")
        lines = fp.readlines()
        for line in lines:
            cols = line.split()
            if len(cols) < 7:
                continue
            # ディクショナリに格納する
            # cols[0]: Filesystem
            # cols[1]: Capacity
            # cols[2]: Used
            # cols[3]: Available
            # cols[4]: Average
            # cols[5]: Mounted
            pre_storage[cols[1]] = (cols[2], cols[3], cols[4], cols[5], cols[6],cols[0])
        fp.close()
    return pre_storage

def check_storage(cur_storage, pre_storage):
    # 現在のストレージ状況をsyslogに出力する
    for key in cur_storage.keys():
        massage = "%s: %s (Avail: %s mb) Capa: %s mb" % (cur_storage[key][4], cur_storage[key][3], cur_storage[key][2], cur_storage[key][0])
        syslog.openlog(ident=__file__, facility=syslog.LOG_LOCAL0)
        syslog.syslog(syslog.LOG_INFO, massage)
        syslog.closelog()
        logger.info(massage)

        # From compare rates equation
        # If use data X bypes in T second
        # If full data have Y bypes, it'll use all data in  (Y * T)/X
        # Example If use data 20 mb in 5 seconds, if data have 100 mb the data will lost in (100*5)/20 = 20 seconds
        # And then we chanage unit from second to day by multiply by 86400
        # The equation is (current available storage * differcence unix time ) / (Difference available storage * 86400)

        diffavail = float(pre_storage[key][2]) - float(cur_storage[key][2]) # To find data used, compare between previuos available and current available
        difftime = int(time.time())-float(pre_storage[key][5]) # To find diffence of time in second unit, compare between previous unix time (/tmp/storage.txt) and current unix time
        if(float(diffavail != 0)): # Python can not divide by 0
            x = float(cur_storage[key][2]) / float(diffavail) # To find time which will use all of data, use equation above
            expectsecond = float(x) * difftime
            expectday = expectsecond/86400 # change to day unit
            if(expectday>DIFF_DAY): # Compare between predict day and DIFF day which can set on the top on source code
                massage = "%s: %s (Avail: %s mb) Capa: %s mb" % (cur_storage[key][4], cur_storage[key][3], cur_storage[key][2], cur_storage[key][0])
                syslog.openlog(ident=__file__, facility=syslog.LOG_LOCAL0)
                syslog.syslog(syslog.LOG_WARNING, massage)
                syslog.closelog()
                logger.warning(massage)
            
def check_inode(cur_storage):
    for key in cur_storage.keys():
        # ファイルシステム毎にtouchコマンドを実行し、ファイルが生成できるか
        # 確認する。ファイルが生成できない場合、i-nodeが枯渇している可能性が
        # あるため、syslogを送信する。
        file_path = ""
        if cur_storage[key][4] == "/":
            file_path = "%s%s" % (cur_storage[key][4], TOUCH_TMP_FILE_NAME)
        else:
            file_path = "%s/%s" % (cur_storage[key][4], TOUCH_TMP_FILE_NAME)

        cmd = "touch %s" % file_path
        stdout_data, stderr_data = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
        logger.info("Execute command: [%s] [stderr:%s]" % (cmd, stderr_data.strip()))

        # 標準エラー出力に文字列が入っていた場合はエラー
        check_err = stderr_data.strip()
        if len(check_err) > 0:
            massage = "[%s] touch command error. (%s)" % (cur_storage[key][4], check_err)
            syslog.openlog(ident=__file__, facility=syslog.LOG_LOCAL0)
            syslog.syslog(syslog.LOG_ERR, massage)
            syslog.closelog()
            logger.error(massage)
        else:
            # touchしたファイルを削除する
            os.remove(file_path)

def save_storage_info(cur_storage):
    fp = open(PREV_INFO_FILE_PATH, "w")
    for key in cur_storage.keys():
        line = "%s %s %s %s %s %s %s\n" % (
                int(time.time()), key, cur_storage[key][0], cur_storage[key][1], cur_storage[key][2], 
                cur_storage[key][3], cur_storage[key][4])
        fp.write(line)
    fp.close()

if __name__ == '__main__':
    main()
