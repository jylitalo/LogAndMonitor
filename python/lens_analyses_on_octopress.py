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

class LensFromEXIF(object):
  def __init__(self):
    self.debug = False

  def process_file(self,img_name):
    assert os.access(img_name, os.R_OK), "Need read access on " + img_name
    f = open(img_name)
    tags = exifread.process_file(f, details=False)
    f.close()

    fl = dt = lens = None
    if tags.has_key("EXIF DateTimeOriginal"): dt = tags["EXIF DateTimeOriginal"].values
    if tags.has_key("EXIF FocalLength"): fl = tags["EXIF FocalLength"].values[0].num
    if tags.has_key("EXIF LensModel"): lens = tags["EXIF LensModel"].values.strip()

    errmsg = None
    if not (dt or fl): errmsg = "DateTime and FocalLength are"
    elif not dt: errmsg = "DateTime is"
    elif not fl: errmsg = "FocalLength is"
    if errmsg: raise AssertionError(errmsg + " missing from " + img_name)

    dt = dt[:10].replace(':','-')
    return dt,self._lens_name(fl,lens)

  @staticmethod
  def _lens_name(focal_length,lens):
    oly12 = "Olympus M.Zuiko 12mm f/2"
    pl25 = "Panasonic Leica DG Summilux 25mm f/1.4"
    oly60 = "Olympus M.Zuiko 60mm f/2.8 Macro"
    lenses_by_model = { "OLYMPUS M.12-50mm F3.5-6.3" : "Olympus M.Zuiko 12-50mm f/3.5-6.3",
                        "OLYMPUS M.75-300mm F4.8-6.7 II" : "Olympus M.Zuiko 75-300mm f/4.8-6.7 II",
                        "OLYMPUS M.12mm F2.0" : oly12,
                        "LEICA DG SUMMILUX 25/F1.4" : pl25,
                        "OLYMPUS M.60mm F2.8 Macro" : oly60 }
    if lens:
      if lens in lenses_by_model: return lenses_by_model[lens]
      print "### No pretty name for >%s<" % (lens)
    else:
      print "### No lens info but focal length was " + str(focal_length)
    lenses_by_fl = { 12 : oly12, 25 : pl25, 60 : oly60 }
    if focal_length in lenses_by_fl: return lenses_by_fl[focal_length]
    raise AssertionError("Unable to map lens name for (%s,%s)" % (str(focal_length),lens))

class LensAnalysesOnOctopress(LensFromEXIF):
  def map_filename(self,fname):
    """ 
      Map filename in blog post to filename into original image with 
      EXIF information. 
    """
    return os.path.expanduser(fname.replace("/images/","~/kuvat/jpg/",1).replace('_c.jpg','.jpg'))

  def scan(self,dir):
    lenses = {}
    for fname in glob.glob("%s%s*.markdown" % (dir,os.sep)):
      if self.debug: print("### Checking " + fname)
      f = open(fname)
      url_name = "/" + os.path.basename(fname)[11:-9] + "/"
      """ 
        Cut off date (yyyy-mm-dd) from beginning and 
        '.markdown' from end of filenames. 
      """
      status = 0
      title = lens = None
      for line in f:
        """
          status = 0 ... beginning of blog post
          status = 1 ... within blog post header
          status = 2 ... within blog post body
        """
        if line.startswith("---"): status += 1
        elif status == 1 and line.startswith("title: "): 
          title = line[7:].strip()
          if title.startswith("'"): title = title[1:-1]
        elif status == 2 and line.startswith("!["):
          img_name = line.split('](',1)[1].split(')',1)[0]
          full_img_name = self.map_filename(img_name)
          assert os.access(full_img_name, os.R_OK), "Unable to read img_file (%s) from %s" % (img_name,fname)
          try:
            dt,lens = self.process_file(full_img_name)
          except AssertionError: lens = "Missing"
          break
      f.close()
      if lens in lenses: lenses[lens].append((url_name,title))
      else: lenses[lens] = [(url_name,title)]
    return lenses
    
if __name__ == '__main__':
  op = assets_on_octopress.Octopress
  dir = op.find_source_dir()
  ofname = sys.argv[1]
  if os.access(ofname, os.F_OK):
    print("File (%s) already exists." % (ofname))
    sys.exit(1)
  lenses = LensAnalysesOnOctopress().scan(dir + "/_posts")
  """ create report from dictionary """
  f = open(ofname,"w")
  f.write(op.head(time.strftime("%Y-%m-%d 12:00:00"),"page","Posts by lens"))
  k = lenses.keys()
  k.sort()
  for lens in k:
    f.write("<div><b>%s (%d)</b><br />\n" % (lens,len(lenses[lens])))
    for url,name in lenses[lens]:
      f.write('<a href="%s">%s</a><br />\n' % (url,name))
    f.write('</div>\n')
  f.close()
