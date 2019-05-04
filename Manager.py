#!/usr/bin/python

from os import listdir
from os.path import isfile, join
from os import walk
import os
from datetime import datetime
import re
import argparse
#import lmutils

LOG_PATH="/var/log"

#
# Function:     getArgs
# Description:  check for cli args and maybe do something?
# Params:       none
# Returns:      none
# TODO          add more args -- any suggestions?
# Args:         -h -l
#
def getArgs():

    parser = argparse.ArgumentParser(description = "command line log manager")
    parser.add_argument("-l", "--log", help = "specify (each) log # to grab from command line", action="store", type = int, nargs="+")
    args = parser.parse_args()
    # TODO get these to the print function somehow, its late and im tired
    #if args.log:
        #print(args.log)

# Function: listLogs
# Description: list the available lgofiles on the system in LOG_PATH
#              the log files have been narrowed down to apache2, auth, and kern
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
    # filter for the logs apache2, auth and kern
    for log in f:
        parts=log.split('.')
        filterlogs=["/var/log/auth","/var/log/apache2/access","/var/log/kern"]
        if len(parts)==1 or (len(parts)==2 and parts[1]=='log'):
            if parts[0] in filterlogs:
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
    os.system('clear')
    print'-'*80+'\nPrint Logs\n'+'-'*80
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
# Function: LoginStatistics
# Description: provide stats about logins using auth.log
#
# Params: none
# Return: none
def authStats():
    os.system('clear')
    print'-'*80+"\nLogin Statistics\n"+'-'*80
    logs = listLogs()
    if "/var/log/auth.log" not in logs:
        print "This system does not have the auth.log log"
        return
    c=["/var/log/auth.log"]
    entries = readLogs(c)

    logins=0
    loginusers=[]
    sshlogins=0
    sshloginusers=[]
    sshconnectionIPs=[]
    newusers=[]

    for entry in entries:
        newlogin = ".* systemd-logind.* New session.*"
        p = re.compile(newlogin)
        result=p.search(entry)
        if result:
            result= result.group(0)
            logins+=1
            s = result.split(" ")[-1][:-1]
            time = getTime(entry)
            if s not in loginusers:
                loginusers.append(s)
            print s+" logged in on "+str(time)
        result=''
        sshlogin = ".* sshd.* session opened.*"
        p = re.compile(sshlogin)
        result=p.search(entry)
        if result:
            result=result.group(0)
            sshlogins+=1
            s = result.split(" ")[-3]
            if s not in sshloginusers:
                sshloginusers.append(s)
            print s+" connected via ssh "+str(getTime(entry))
        result=''
        ipaddr="[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"
        p = re.compile(ipaddr)
        result=p.search(entry)
        if result:
            if "sshd" in entry and "from" in entry:
                result=result.group(0)
                if result not in sshconnectionIPs:
                    if "Failed" in entry or "Invalid" in entry:
                        print result+" Failed to login to ssh at"+str(getTime(entry))
                    else:
                        print result+" logged into ssh at"+str(getTime(entry))
                    sshconnectionIPs.append(result)
        if "new user" in entry:
            print "New user created "+entry.split(" ")[10][:-1]+" at "+str(getTime(entry))
            newusers.append(entry.split(" ")[10][5:-1])

    print"\n"
    print("-"*80)

    print str(logins)+" logins"
    print "\nusers that logged in:"
    for u in loginusers:
        print u

    print"\n"
    print("-"*80)

    print str(sshlogins)+" ssh logins"
    print "\nssh users that logged in:"
    for u in sshloginusers:
        print u
    
    print"\n"
    print("-"*80)

    print "IPs that connected to ssh:"
    for ip in sshconnectionIPs:
        print ip
    
    print"\n"
    print("-"*80)

    print "New Users created:"
    for u in newusers:
        print u
    print"\n"

#
# Function: mainmenu
# Description: main menu to drive the program
#
# Params: none
# Returns:
def mainmenu():
    os.system('clear')
    print('-'*80+"\nLog Reader\n"+'-'*80)
    print("1) Read Logs")
    print("2) Login Statistics")
    print("3) Apache statistics")
    print("-1) exit")
    uinput = raw_input("\nEnter the number of the above operation to perfrom:\n")

    if int(uinput)==-1:
        exit(0)
    if int(uinput)==1:
        c=userChoice()
        os.system('clear')
        entries = readLogs(c) # may make a seperate function for this if we add filters
        for entry in entries:
            print entry
    elif int(uinput)==2:
        authStats()
    else:
        exit(0)

#
# Function: getTime
# Description: use regex to try to get date and time from logs
# 
# Params: entry - log enrty
# Returns: date
def getTime(entry):
    
    date=''
    if entry.split(" --- ")[0] == "/var/log/apache2/access.log":
        typeApache = "[0-9]{2}/[a-zA-Z]{3,9}/[0-9]{4}:[0-9]{2}:[0-9]{2}:[0-9]{2}"
        p = re.compile(typeApache)
        result = p.search(entry)
        result = result.group(0)
        date = datetime.strptime(result, '%d/%B/%Y:%H:%M:%S')
    else:
        typeAuth = "[a-zA-Z]{3,9} [0-9\s][0-9] [0-9]{2}:[0-9]{2}:[0-9]{2}"
        p = re.compile(typeAuth)
        result = p.search(entry)
        result = result.group(0)
        date = datetime.strptime(result, '%b %d %H:%M:%S').replace(year=2019)
    
    return date

#
# Function: timeCompare
# Description: use getTime to compare the time of two entries
# Params: a - first entry
#         b - second entry
# returns: 1 or -1 based on compare
def timeCompare(a,b):
    if getTime(a) > getTime(b):
        return 1
    else:
        return -1
        
#
# Function: readLogs
# Description: read logs associated with the indexes chosen by the user
# at some point this function may have another parameter/s for filters
#
# Params: logs - the list of logs to print
#
# Returns: entries - list of entries
def readLogs(logs):
 
    entries=[]
    for i in logs:
        infile = open(i,'r')
        lines=infile.readlines()
        for line in lines:
            entries.append(i+" --- "+line)
        infile.close()
    entries.sort(timeCompare)
    return entries

mainmenu()
#getArgs()

