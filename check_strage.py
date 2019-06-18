import itertools
import os
from logging.handlers import SysLogHandler
import logging
import re
import subprocess

DIFF_VALUE=1000

def readcommand():
    cmd = "df -m --portability"
    ret = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).communicate()[0]
    currword = ret.split()
    currwordlist = [ currword[i:i+6] for i in range(7, len(currword), 6) ]
    return currword,currwordlist
    
def check_exist(prevwordlist):
    if os.path.exists('/tmp/strage.txt'):
        save_path1 ='/tmp'
        openname1 = os.path.join(save_path1,"strage.txt")
        fp1 = open(openname1,"r")
        fpread1 = fp1.read()
        prevword = fpread1.split()
        prevwordlist = [ prevword[i:i+6] for i in range(7, len(prevword), 6) ]
        return prevwordlist
    else:
        prevword = currword
        prevwordlist = [ prevword[i:i+6] for i in range(7, len(prevword), 6) ]
        return prevwordlist

def writefile(currwordlist,prevwordlist):
    logging.basicConfig(filename='/var/log/Pom.log',level=logging.DEBUG,filemode='a',datefmt='%m-%d %H:%M',format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    save_path ='/tmp'
    openname = os.path.join(save_path,"strage.txt")
    f = open(openname,"w")
    f.write("Filesystem           1K-blocks     Used Available Use% Mounted on\n")
    countline = int(len(currwordlist)) 

    i=0
    while (i < countline):
        k=0
        while (k<1):
            valuesplit = currwordlist[i]
            valuesplit1 = prevwordlist[i]
            used = float(valuesplit[2])*0.0001
            ava = float(valuesplit[3])*0.0001
            print >>f, valuesplit[0],'\t',valuesplit[1],'\t',valuesplit[2],'\t',valuesplit[3],'\t',valuesplit[4],'\t',valuesplit[5]
            used = str(round(used,2))
            ava = str(round(ava,2))
            checkava = float(valuesplit1[3])-float(valuesplit[3])
            if checkava>DIFF_VALUE:
                logging.warning('%s:Diff value: %s',valuesplit[0],checkava)
                print("Warnning::::Diff value at ",valuesplit[0],checkava)
            logging.info('%s:C %sG:A %sG:%s',valuesplit[0],used,ava,valuesplit[4])      
            k+=1
        i+=1

currword,currwordlist = readcommand()
prevwordlist = check_exist(currword)
writefile(currwordlist,prevwordlist)


