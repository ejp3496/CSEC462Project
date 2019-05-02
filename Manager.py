#!/usr/bin/python

from os import listdir
from os.path import isfile, join
from os import walk
import re

LOG_PATH="/var/log"

#
# Function: listLogs
# Description: list the available lgofiles on the system in LOG_PATH
# Params: none
# Returns: list of current log files 
#
def listLogs():
    f=[]
    for (dirpath, dirname, filenames) in walk(LOG_PATH,topdown=False):
        # skipping journal for now might have to use journalctl
        if "journal" in dirpath:                
            continue
        for name in filenames:
            f.append(join(dirpath,name))

    logs=[]

    # add only current logs (i.e. not logs like foo.log.1 or foo.log.2.gz)
    # may need a function to go back further in logs using those files
    for log in f:
        parts=log.split('.')
        if len(parts)==1 or (len(parts)==2 and parts[1]=='log'):
            logs.append(log)
    return logs

#
# Function: userChoice
# Description: ask for user input. Parse input find logs to list
# This function will probobly be chnaged and added to.
# I would guess that over time the user will input different commands or flags
# we could also change this to work as command line args
#
# Params: none
# Returns: list of indexes of logs to list (this is subject to change)
def userChoice():

    count=0
    logs = listLogs()
    for log in logs:
        print(str(count)+". "+str(log))
        count+=1    


    usrinput = raw_input("\nEnter the numbers of the logs to print (ex. 1-4,10,12)\n")

    chosenlogs=[]
    
    # no error checking yet
    parts = usrinput.split(',')
    for part in parts:
        if '-' not in part:
            chosenlogs.append(logs[int(part)])
        else:
            temp = part.split('-')
            for i in range(int(temp[0]),int(temp[1])+1):
                chosenlogs.append(logs[i])
    return chosenlogs

#
# Function: getTime
# Description: use regex to try to get date and time from logs
# 
# Params: entry - log enrty
# Returns: date 
# this function is not finished. It is going to take some time to exttract date and time 
# from many different types of logs. Each log seems to have a varying format. 
# We may want to think about narrowing the scope to only deal with common/popular logs.
def getTime(entry):
    
    type1 = re.compile("[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}")
    type2 = re.compile("[a-zA-Z]{3} [0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}")
    type3 = re.compile("[0-9]{2}/[a-zA-Z]{3}/[0-9]{4}:[0-9]{2}:[0-9]{2}:[0-9]{2}")
    type4 = re.compile("[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}")

#
# Function: printLogs
# Description: print logs associated with the indexes chosen by the user
# at some point this function may have another parameter/s for filters
#
# Params: logs - the list of logs to print
#
# Returns: none
def printLogs(logs):
 
    for i in logs:
        infile = open(i,'r')
        lines=infile.readlines()
        print(i+":")
        for line in lines[-10:]:
            print("| "+line)
        infile.close()


c = userChoice()
printLogs(c)
