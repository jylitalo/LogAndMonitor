#!/usr/bin/python

import glob
import os
import sys
import time

import assets_on_octopress

def get_head(assets,title,first):
  d = time.strftime("%Y-%m-%d")
  title = "%s (#%d-%d/365)" % (title,first,first+19)
  return assets.head(d + " 12:00:00","page",title)

def parse_post(fname):
  f = open(fname)
  title = img = None
  for line in f:
    if line.startswith("title: "): title = line[len("title: "):line.find("(")]
    elif "_c.jpg)" in line: img = line[line.find("(/")+1:line.find("_c.jpg")]
    if img and title: break
  f.close()
  return img,title

if __name__ == '__main__':
  first = int(sys.argv[1])
  title = sys.argv[2]

  assets = assets_on_octopress.AssetsFixer()
  dir = assets.find_source_dir()
  target_dir = "%s/%d-%d" % (dir,first,first+19)
  if not os.access(target_dir,os.F_OK): os.mkdir(target_dir)

  f = open(target_dir + "/index.markdown","w")
  f.write(get_head(assets,title,first))
  f.write("[#%d-%d](/%d-%d/)\n\n" % (first-20,first-1,first-20,first-1))
  fname_list = glob.glob(dir + "/_posts/*.markdown")
  for i in range(first,first+20):
    # print("### %d: %s" % (i,fname_list[i-1]))
    fname = fname_list[i-1]
    img,title = parse_post(fname)
    url = assets.get_url(fname)
    f.write("[{%% img %s_t.jpg #%d %s %%}](/%s/)\n" % (img,i,title,url))
  f.close()

  assets.scan()
  assets.validate()
