#!/usr/bin/python

###
# Analyze ssh connections from /var/log/secure*
###
import getopt
import glob
import os
import sys

###
# Add IP number (ip) into dictionary (results)
# If IP address is in format a.b.c.d, it will be added into dictionary as
# a.0.0.0/8
# a.b.0.0/16
# a.b.c.0/24
# a.b.c.d
###
def increment_numbers(results,ip):
    ip_numbers = ip.split('.')
    assert(len(ip_numbers) == 4, "ip (%s) doesn't have four numbers" % (ip))
    network = [24,16,8]
    rounds = 0
    suffix = ""
    while ip_numbers:
        ip_dots = '.'.join(ip_numbers)
        if rounds: ip_dots += "%s/%d" % (".0" * rounds, network[rounds-1])
        if ip_dots in results: results[ip_dots] += 1
        else: results[ip_dots] = 1
        ip_numbers.pop(-1)
        rounds += 1

###
# print results to standard output
# if a.b.c.d has same number as in a.b.c.0/24, we skip a.b.c.0/24
# if a.b.c.0/24 has same number as in a.b.0.0/16, we skip a.b.0.0/16
# if a.b.0.0/16 has same number as in a.0.0.0/8, we skip a.b.0.0/8
###
def print_report(results):
    key_list = results.keys()
    key_list.sort()
    key_list.reverse()
    prev = 0
    prev_key = ""
    valid_keys = []
    for k in key_list:
        if results[k] != prev:
            valid_keys.append(k)
            prev = results[k]
            prev_key = k
    valid_keys.sort()
    for k in valid_keys:
        print "%s : %d" % (k,results[k])

###
# scan file (fname) and calculate figures into dictionaries.
# Search patterns are:
# [timestamp] [hostname] sshd[8316]: Received disconnect from a.b.c.d: 11: Bye Bye
# [timestamp] [hostname] sshd[3963]: Did not receive identification string from a.b.c.d
# [timestamp] [hostname] sshd[8239]: Invalid user abc from a.b.c.d
# [timestamp] [hostname] sshd[14973]: Accepted publickey for myaccount from a.b.c.d port 50412 ssh2
###
def scan_file(fname,received_disconnect,no_identification,invalid_user,accepted_pubkey):
    f = open(fname)
    for line in f:
        if 'sshd' in line:
            line = line.strip()
            if 'Received disconnect from' in line:
                ip = line.split(':')[-3].split(' ')[-1]
                increment_numbers(received_disconnect,ip)
            elif 'Did not receive identification string from' in line:
                increment_numbers(no_identification,line.split(' ')[-1])
            elif ']: Invalid user' in line:
                ip = line.split(' ')[-1]
                increment_numbers(invalid_user,ip)
            elif 'Accepted publickey for' in line:
                ip = line.split(' ')[-4]
                increment_numbers(accepted_pubkey,ip)
            else:
                # print '### ' + line
                pass
    f.close()
    
if __name__ == '__main__':
    received_disconnect = {}
    no_identification = {}
    invalid_user = {}
    accepted_pubkey = {}
    ###
    # args
    ###
    opts,args = getopt.getopt(sys.argv[1:],'a',['all'])
    all = 0
    for key,arg in opts:
        if key == '-a' or key == '--all': all = 1
    ###
    # filenames to be scanned
    ###
    if all: fnames = glob.glob("/var/log/secure*")
    else: fnames = ["/var/log/secure"]
    for fname in fnames:
        scan_file(fname,received_disconnect,no_identification,invalid_user,accepted_pubkey)
    ###
    # reporting
    ###
    for k,d in [("received disconnect",received_disconnect),
                ("no_identification",no_identification),
                ("invalid_user",invalid_user),
                ("accepted_public",accepted_pubkey)]:
        print "### " + k
        print_report(d)
    sys.exit(0)
