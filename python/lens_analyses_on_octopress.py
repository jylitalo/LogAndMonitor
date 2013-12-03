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

class LensAnalysesOnOctopress(object):
  def __init__(self):
    self.debug = False

  def process_file(self,fname):
    """ 
      Check if _fname_ has EXIF information with focal length that was used 
      in camera, when photo was taken.
      Return None, if focal length was not found
      Return focal length as string with "mm" suffix, if focal length was found.
    """
    if self.debug: print("### processing " + fname)
    fl_name = "EXIF FocalLength"
    f = open(fname)
    tags = exifread.process_file(f, stop_tag=fl_name, details=False)
    f.close()
    if not tags.has_key(fl_name): return None
    fl = tags[fl_name]
    if self.debug: print("### %s -> %d" % (fname,fl))
    if fl > 60: fl=75
    return str(fl) + "mm"

  def map_filename(self,fname):
    """ 
      Map filename in blog post to filename into original image with 
      EXIF information. 
    """
    return os.path.expanduser(fname.replace("/images/","~/kuvat/jpg/",1).replace('_c.jpg','.jpg'))

  def scan(self,dir):
    focal_lengths = {'missing':[]}
    for fname in glob.glob("%s%s*.markdown" % (dir,os.sep)):
      if self.debug: print("### Checking " + fname)
      f = open(fname)
      url_name = "/" + os.path.basename(fname)[11:-9] + "/"
      """ 
        Cut off date (yyyy-mm-dd) from beginning and 
        '.markdown' from end of filenames. 
      """
      status = 0
      title = None
      fl = None
      for line in f:
        """
          status = 0 ... beginning of blog post
          status = 1 ... within blog post header
          status = 2 ... within blog post body
        """
        if line.startswith("---"): status += 1
        elif status == 1 and line.startswith("title: "): 
          title = line[7:].strip()
        elif status == 2 and line.startswith("!["):
          img_name = line.split('](',1)[1].split(')',1)[0]
          full_img_name = self.map_filename(img_name)
          assert os.access(full_img_name, os.R_OK), "Unable to read img_file (%s) from %s" % (img_name,fname)
          fl = self.process_file(full_img_name)
          break
      f.close()
      if not fl: focal_lengths['missing'].append((url_name,title))
      elif fl in focal_lengths: focal_lengths[fl].append((url_name,title))
      else: focal_lengths[fl] = [(url_name,title)]
    return focal_lengths
    
if __name__ == '__main__':
  op = assets_on_octopress.Octopress
  dir = op.find_source_dir()
  ofname = sys.argv[1]
  if os.access(ofname, os.F_OK):
    print("File (%s) already exists." % (ofname))
    sys.exit(1)
  focal_lengths = LensAnalysesOnOctopress().scan(dir + "/_posts")
  """ create report from dictionary """
  lens_name = {
      "missing" : "Not available",
      "12mm" : "Olympus M.Zuiko 12mm f/2",
      "25mm" : "Panasonic Leica DG Summilux 25mm f/1.4",
      "60mm" : "Olympus M.Zuiko 60mm f/2.8 Macro",
      "75mm" : "Olympus M.Zuiko 75-300mm f/4.8-6.7 II"
      }
  k = lens_name.keys()
  k.sort()
  f = open(ofname,"w")
  f.write(op.head(time.strftime("%Y-%m-%d 12:00:00"),"page","Posts by lens"))
  for fl in k:
    f.write("<div><b>%s (%d)</b><br />\n" % (lens_name[fl],len(focal_lengths[fl])))
    for url,name in focal_lengths[fl]:
      f.write('<a href="%s">%s</a><br />\n' % (url,name))
    f.write('</div>\n')
  f.close()
