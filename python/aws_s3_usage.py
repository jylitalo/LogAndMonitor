#!/usr/bin/python

import glob
import os
import sys

class AWS_S3_Usage:
  def __init__(self):
    self.file_stats = {}
    self.user_agent = {}
    self.total_bytecount = 0
    self.ignored_operations = ["REST.DELETE.OBJECT","REST.GET.BUCKET","REST.PUT.LOGGING_STATUS","REST.PUT.OBJECT","REST.PUT.WEBSITE","WEBSITE.HEAD.OBJECT"]
    self.ignored_statuses = ["301","304"]

  def _split_line(self,line):
    line = line.strip()
    # print("--- " + line)
    if not line: return None
    fields = []
    cur = None
    for field in line.split(' '):
      # print("### " + field)
      if cur:
        if not field: cur += "  "
        elif field[-1] == '"' or field[-1] == ']':
          fields.append(cur + " " + field)
          cur = None
        else: cur += " " + field
      elif field[0] == '"' and field[-1] != '"': cur = field
      elif field[0] == '[' and field[-1] != ']': cur = field
      else:  fields.append(field)
    if cur: fields.append(cur)
    return fields

  def scan(self, dir):
    # 0 bucket owner (not interesting)
    BUCKET = 1 
    # 2 timestamp
    # 3 remote ip
    # 4 requester ?
    # 5 request id ?
    OPERATION = 6
    FILE_NAME = 7
    # 8 HTTP request
    HTTP_STATUS = 9
    # 10 error code (or -)
    BYTES_SENT = 11
    # 12 object size
    # 13 total time
    # 14 turn-around time
    # 15 referrer
    USER_AGENT = 16
    # 17 version id
    for fname in glob.glob("%s/*" % (sys.argv[1])):
      f = open(fname,"r")
      for line in f:
        fields = self._split_line(line)
        if not fields or len(fields) < 18: continue
        uri = fields[BUCKET] + "/" + fields[FILE_NAME]
        bytecount = 0
        user_agent = fields[USER_AGENT]
        # if fields[FILE_NAME] == '-': print("### " + line)
        if fields[OPERATION] in self.ignored_operations: pass
        elif fields[HTTP_STATUS] in self.ignored_statuses: pass
        else: bytecount = int(fields[BYTES_SENT])
        self.total_bytecount += bytecount

        if uri in self.file_stats:
          self.file_stats[uri][0] += bytecount
          self.file_stats[uri][1] += 1
        else:
          self.file_stats[uri] = [bytecount,1]
        if user_agent in self.user_agent:
          self.user_agent[user_agent][0] += bytecount
          self.user_agent[user_agent][1] += 1
        else:
          self.user_agent[user_agent] = [bytecount,1]
        # print("?!? %s : %d => %d" % (uri,bytecount,file_stats[uri][0]))

  def _organize_by_size(self,stats):
    by_size = {}
    for key in stats:
      bytecount = stats[key][0]
      msg = "%s (%d)" % (key, stats[key][1])
      if bytecount in by_size: by_size[bytecount].append(msg)
      else: by_size[bytecount] = [msg]
    return by_size

  def _print_report(self, stats):
    files_by_size = self._organize_by_size(stats)
    if 0 in files_by_size: del files_by_size[0]
    size_list = files_by_size.keys()
    size_list.sort()
    size_list.reverse()
    for size in size_list:
      mb = size / (1024*1024)
      fnames = files_by_size[size]
      fnames.sort()
      for fname in fnames:
        print("%d (%d MB / %.2f%%): %s" % (size,mb,100.0*size/self.total_bytecount,fname)) 
    print("%d (%d MB) in TOTAL" % (self.total_bytecount, self.total_bytecount / (1024*1024)))

  def files_report(self): self._print_report(self.file_stats)
  def agent_report(self): self._print_report(self.user_agent)

if __name__ == '__main__':
  s3 = AWS_S3_Usage()
  s3.scan(sys.argv[1])
  print("BANDWIDTH USAGE BY URI")
  print("======================")
  s3.files_report()
  print("")
  print("BANDWIDTH USAGE BY USER-AGENT")
  print("=============================")
  s3.agent_report()
