#!/usr/local/bin/python

import glob
import os
import sys
import time

# on Mac OS X:
# brew install python
# pip install exifread
# use python from /usr/local/bin (instead of /usr/bin/python)
import exifread

import assets_on_octopress

def process_file(fname):
  fl = dt = None
  f = open(fname)
  tags = exifread.process_file(f)
  f.close()

  if tags.has_key("EXIF DateTimeOriginal"): dt = tags["EXIF DateTimeOriginal"].values
  if tags.has_key("EXIF FocalLength"): 
    fl = tags["EXIF FocalLength"].values[0].num
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
  year,month = datetime[:4],datetime[5:7]
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
  title = "%s (%d/365)" % (subject,days)
  assets = assets_on_octopress.AssetsFixer()
  fname = post_fname(assets.find_source_dir(),datetime,subject)
  f = open(fname,"w")
  f.write('''%s![%s](%s)
<!--more-->
%s
''' % (assets.head(datetime + " 12:00:00",'post',title),subject,img_fname,lens))
  f.close()
  print "### %s written." % (fname)
  assets.scan()
  assets.validate()
