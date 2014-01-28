#!/usr/bin/python
from boto.dynamodb2.fields import HashKey, RangeKey
from boto.dynamodb2.table import Table
from boto.dynamodb2.exceptions import ConditionalCheckFailedException
from boto.exception import JSONResponseError
from math import sqrt
from pprint import pprint
from time import sleep
import simplejson as js
import sys

Tests = [
    "Dhrystone 2 using register variables",  # dhrystone
    "Double-Precision Whetstone",            # double
    "Execl Throughput",                      # execl
    "File Copy 1024 bufsize 2000 maxblocks", # file1024
    "File Copy 256 bufsize 500 maxblocks",   # file256
    "File Copy 4096 bufsize 8000 maxblocks", # file4096
    "Pipe Throughput",                       # pipethru
    "Pipe-based Context Switching",          # pipecs
    "Process Creation",                      # process
    "Shell Scripts (1 concurrent)",          # shell1
    "Shell Scripts (8 concurrent)",          # shell8
    "System Call Overhead",                  # overhead
    "System Benchmarks Index Score"          # index
]

TestsAbbr = [
    "dhrystone",
    "double",
    "execl",
    "file1024",
    "file256",
    "file4096",
    "pipethru",
    "pipecs",
    "process",
    "shell1",
    "shell8",
    "overhead",
    "index"
]

TRIAL = 5

def parse_log(log):
    if "multi" in log:
        parallel = ["single", "multi"]
    else:
        parallel = ["single"]

    logdict = {}

    for p in parallel:
        for t in range(0,len(Tests)):
            d_sum = 0
            d_arr = []
            for i in range(0,TRIAL):
                val = log[p][i][TestsAbbr[t]]
                d_sum += val
                d_arr.append(val)
            mean = d_sum/len(d_arr)
            sd_sum = 0
            for i in d_arr:
                sd_sum += i*i
            sd = sqrt(sd_sum/(len(d_arr)-1))
            if p not in logdict:
                logdict[p] = {}
            logdict[p][Tests[t]] = {"Mean": mean, "SD": sd}

    return logdict

def main():
    logs = {}

    # Retrieve instance information
    try:
        instances = Table('instances')
        instances.describe()
    except JSONResponseError:
        print "Instance information retrieval failed. Check the 'instances' table"
        sys.exit(1)

    for item in instances.scan():
        instance_name = item['Instance Name']
        log_raw = {}
        try:
            instance_logs = Table(instance_name)
            for l in instance_logs.scan():
                for t in range(0,len(Tests)):
                    if l['parallel'] not in log_raw:
                        log_raw[l['parallel']] = {}
                    if int(l['trial']) not in log_raw[l['parallel']]:
                        log_raw[l['parallel']][int(l['trial'])] = {}
                    log_raw[l['parallel']][int(l['trial'])][TestsAbbr[t]] = float(l[Tests[t]])
        except JSONResponseError:
            print "No log was found for %s" % instance_name
            sys.exit(1)

        #pprint(log_raw)
        logs[instance_name] = parse_log(log_raw)

    print js.dumps(logs, indent=4*' ')

if __name__ == "__main__":
    main()