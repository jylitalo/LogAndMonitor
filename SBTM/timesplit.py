###
# timesplit.py is tool for analysing what percentage of RapidReporter session time was spent on 
# setup, bug, check and test states. Other information in RapidReporter log files is simply ignored.
#
# Arguments:
# 1st argument is filename of RapidRepoter log file.
# Output:
# Report is sent to standard output (stdout).
###

import os
import sys
import time

def parse_timestamp(timestamp):
  t = time.strptime(timestamp,"%d.%m.%Y %H:%M:%S")
  return time.mktime(t)

if __name__ == '__main__':
  fname = sys.argv[1]
  states = ["Setup","Bug","Check","Test"]
  time_per_state = {}
  for state in states: time_per_state[state] = 0
  state = None
  state_started = None
  file_started = None

  f = open(fname)
  for line in f:
    timestamp,reporter,type,content,screenshot,rtfnote = line.split(',')
    if timestamp == "Time": continue
    t = parse_timestamp(timestamp)
    if not state: 
      state_started = file_started = t
      state = states[0]
    elif type == "Session End. Duration":
      time_per_state[state] += t-state_started
    elif type in states and type != state:
      time_per_state[state] += t-state_started
      state_started = t
      state = type
  f.close()
  # print("total time=" + content)
  total = 0
  for state in states: total += time_per_state[state]
  for state in states:
    print("%s:\t%ds / %d%%" % (state,time_per_state[state],100*time_per_state[state]/total))
  print("total:\t%ds" % (total))
