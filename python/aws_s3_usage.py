#!/usr/bin/python

import glob
import os
import sys

class AWS_S3_Usage:
  def __init__(self):
    self.file_stats = {}
    self.total_bytecount = 0

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
    # 16 user-agent
    # 17 version id
    ignored_operations = ["REST.DELETE.OBJECT","REST.GET.BUCKET","REST.PUT.LOGGING_STATUS","REST.PUT.OBJECT","REST.PUT.WEBSITE","WEBSITE.HEAD.OBJECT"]
    for fname in glob.glob("%s/*" % (sys.argv[1])):
      f = open(fname,"r")
      for line in f:
        fields = self._split_line(line)
        if not fields or len(fields) < 18: continue
        uri = fields[BUCKET] + "/" + fields[FILE_NAME]
        bytecount = 0
        # if fields[FILE_NAME] == '-': print("### " + line)
        if fields[OPERATION] in ignored_operations: pass
        elif fields[HTTP_STATUS] in ["301","304"]: pass
        else: bytecount = int(fields[BYTES_SENT])
        self.total_bytecount += bytecount

        if uri in self.file_stats:
          self.file_stats[uri][0] += bytecount
          self.file_stats[uri][1] += 1
        else:
          self.file_stats[uri] = [bytecount,1]
        # print("?!? %s : %d => %d" % (uri,bytecount,file_stats[uri][0]))

  def _organize_by_size(self):
    files_by_size = {}
    for key in self.file_stats:
      bytecount = self.file_stats[key][0]
      msg = "%s (%d)" % (key, self.file_stats[key][1])
      if bytecount in files_by_size: files_by_size[bytecount].append(msg)
      else: files_by_size[bytecount] = [msg]
    return files_by_size

  def print_report(self):
    files_by_size = self._organize_by_size()
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

if __name__ == '__main__':
  s3 = AWS_S3_Usage()
  s3.scan(sys.argv[1])
  s3.print_report()
