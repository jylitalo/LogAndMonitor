import glob
import os
import sys
import time

import exifdump
import assets_on_octopress

def process_file(fname):
  fl = dt = None
  f = open(fname)
  data = f.read(12)
  length = ord(data[4])*256 + ord(data[5])
  data = f.read(length-8)
  T = exifdump.TIFF_file(data)
  L = T.list_IFDs()
  for i in range(len(L)):
    exif_off = None
    IFD = T.dump_IFD(L[i])
    for (tag,type,values) in IFD:
      if tag == 0x8769:
        exif_off = values[0]
      elif tag in exifdump.EXIF_TAGS:
        stag = exifdump.EXIF_TAGS[tag]
        if stag == "FocalLength": fl = values[0].num
    if exif_off and not fl:
      IFD = T.dump_IFD(exif_off)
      for (tag,type,values) in IFD:
        if tag in exifdump.EXIF_TAGS:
          stag = exifdump.EXIF_TAGS[tag]
          if stag == "FocalLength":  
            fl = values[0].num
          elif stag == "DateTimeOriginal": dt = values
  f.close()
  if fl > 60: fl=75
  return (fl,dt)

def lens_name(focal_length):
  if focal_length == 12: lens = "Olympus M.Zuiko 12mm f/2"
  elif focal_length == 25: lens = "Panasonic Leica DG Summilux 25mm f/1.4"
  elif focal_length == 60: lens = "Olympus M.Zuiko 60mm f/2.8 Macro"
  else: lens = "UNKNOWN"
  return lens

def image_fname(datetime,fname):
  """
  >>> image_fname("2013-11-11","~/kuvat/jpg/2013/11/PB123456.jpg")
  '/images/2013/11/PB123456_c.jpg'
  """
  year = datetime[:4]
  month = datetime[5:7]
  fname = fname[fname.rfind('/'):fname.rfind('.')]
  return "/images/%s/%s%s_c.jpg" % (year,month,fname)

def post_fname(dir,datetime,subject):
  """
  >>> post_fname("foo/source","2013-11-11","Foo bar")
  'foo/source/_posts/2013-11-11-foo-bar.markdown'
  """
  fname = subject.replace(' ','-').lower()
  fname = "%s/_posts/%s-%s.markdown" % (dir,datetime,fname)
  return fname

if __name__ == '__main__':
  img_fname = sys.argv[1]
  subject = sys.argv[2]

  focal_length,datetime = process_file(img_fname)
  if not datetime: print "### Datetime missing from image (%s)" % (img_fname)
  if not focal_length: print "### Focal length missing from image (%s)" % (img_fname)
  if not datetime or not focal_length:
    raise AssertionError("photograph (%s) doesn't seem to have EXIF for date and/or focal length" % (img_fname))

  # print "datetime = " + datetime
  datetime = datetime[:10].replace(':','-')
  img_fname = image_fname(datetime,img_fname)
  lens = lens_name(focal_length)

  days = time.strptime(datetime,"%Y-%m-%d")[7]
  assets = assets_on_octopress.AssetsFixer()
  fname = post_fname(assets.find_source_dir(),datetime,subject)
  f = open(fname,"w")
  f.write('''---
date: '%s 12:00:00'
layout: post
status: publish
title: %s (%d/365)
---
![%s](%s)
<!--more-->
%s
''' % (datetime,subject,days,subject,img_fname,lens))
  f.close()
  print "### %s written." % (fname)
  assets.scan()
  assets.validate()
