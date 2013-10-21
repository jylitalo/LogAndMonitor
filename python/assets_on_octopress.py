#!/usr/bin/python

import glob
import os
import stat
import sys

class AssetsOnOctopress(object):
  def __init__(self,dir):
    self._dir = dir
    self.debug = False
    self._found = []
    self._linked = {}

  def _extract_from_markdown(self, line):
    for field in line.split("(/")[1:]:
      field = "/" + field[:field.find(')')]
      if ' "' in field: field = field[:field.find(' "')]
      if field.startswith("/images/") or field.startswith("/assets/"):
         if field in self._linked: self._linked[field] += 1
         else: self._linked[field] = 1
    for field in line.split('"/')[1:]:
      field = "/" + field[:field.find('"',1)]
      if field.startswith("/images/") or field.startswith("/assets/"):
         if field in self._linked: self._linked[field] += 1
         else: self._linked[field] = 1

  def _scan_tree(self,subdir):
    ret = []
    ignore = len(self._dir)
    for root,dirnames,filenames in os.walk(self._dir + subdir):
      for filename in filenames:
        if filename == ".DS_Store": pass
        else:
          fname = os.path.join(root, filename)[ignore:]
          self._validate_found(fname)
    return ret

  def scan(self):
    begin_index = len("yyyy-mm-dd")
    end_index = len(".markdown")
    pattern = "%s/_posts/*.markdown" % (self._dir)
    markdown_files = glob.glob(pattern)
    if not markdown_files:
      print("### Unable to find any markdown files from " + pattern)
      sys.exit(1)
    else:
      print("### processing %d markdown files" % (len(markdown_files)))
    for fname in markdown_files:
      if self.debug: print("### Checking " + fname)
      f = open(fname)
      url_name = "/" + os.path.basename(fname)[begin_index:-end_index] + "/"
      """ 
        Cut off date (yyyy-mm-dd) from beginning and 
        '.markdown' from end of filenames. 
      """
      for line in f:
          if "(/images/" in line or "(/assets/" in line:
            self._extract_from_markdown(line)
          elif '"/images/' in line or '"/assets/' in line:
            self._extract_from_markdown(line)
      f.close()
    print("### found %d links" % (len(self._linked)))
    self._scan_tree("/assets/")
    print("### found after /assets/ is %d"% (len(self._found)))
    self._scan_tree("/images/")
    print("### found after /images/ is %d"% (len(self._found)))

  def _validate_found(self, fname): self._found.append(fname)
  def _validate_waste(self,fname): print("WASTE: '%s'" % (fname))
  def _validate_missing(self, fname): print("MISSING: '%s'" % (fname))

  def remove_matches(self):
    # print("found_images = %d" % (len(self._found_images)))
    if self._found: self._found.sort()
    if self._found:
      for fname in self._found:
        if fname in self._linked: del self._linked[fname]
        elif fname.startswith("/assets/jwplayer"): pass
        elif fname.startswith("/images/") and fname.count('/') == 2: pass
        else: self._validate_waste(fname)
    if self._linked: 
      linked_keys = self._linked.keys()
      linked_keys.sort()
      for fname in linked_keys: self._validate_missing(fname)

class ValidateAndFixAssets(AssetsOnOctopress):
  def __init__(self,dir):
    AssetsOnOctopress.__init__(self,dir)
    self._images_root = os.path.expanduser("~/kuvat/original_jpg")

  def _original_image(self,fname):
    begin_index = fname.find('/',1)
    end_index = len("_t.jpg")
    if fname[-end_index] != '_': end_index = len(".jpg")
    # print("begin_index=%d, end_index=%d" % (begin_index,end_index))
    pattern = "%s%s.*" % (self._images_root,fname[begin_index:-end_index])
    original_fname = glob.glob(pattern)
    if original_fname: return original_fname[0]
    original_fname = glob.glob(pattern.replace('/IMG_','/img_'))
    if original_fname: return original_fname[0]
    return None

  def _validate_found(self,fname):
    if fname.startswith("/assets/"): return
    elif fname.startswith("/images/") and fname.count('/') == 2: return
    # print "### validating " + fname
    original_fname = self._original_image(fname)
    if original_fname:
      full_fname = self._dir + fname
      original_mtime = os.stat(original_fname)[stat.ST_MTIME]
      full_mtime = os.stat(full_fname)[stat.ST_MTIME]
      if original_mtime >= full_mtime:
        print("unlink %s (%d vs. %d)" % (full_fname,original_mtime,full_mtime))
        # os.unlink(full_fname)
      else: self._found.append(fname)
    else: 
      print("### unable to find original file for " + fname)

  def _validate_waste(self,fname):
    print("unlinking %s%s (validate waste)" % (self._dir,fname))
    # os.unlink("%s%s" % (self._dir,fname))

  def _resize_image(self,source_name,dest_name,resolution):
    cmdline = "convert -resize %s %s %s" % (resolution,source_name,dest_name)
    print("### " + cmdline)
    os.system(cmdline)

  def _validate_missing(self,fname):
    original_fname = self._original_image(fname)
    fname = self._dir + fname
    if not original_fname:
      print("### unable to find original_image for " + fname)
    if fname.endswith("_t.jpg"):
      cmdline = "convert -thumbnail 150x150^ -gravity center -extent 150x150 %s %s" % (original_fname,fname)
      print("### " + cmdline)
      os.system(cmdline)
    elif fname.endswith("_c.jpg"):
      self._resize_image(original_fname,fname,"750x750")
    elif fname.endswith("_l.jpg"):
      self._resize_image(original_fname,fname,"1024x750")


if __name__ == '__main__':
  dir = sys.argv[1]
  # ofname = sys.argv[2]
  # if os.access(ofname, os.F_OK):
  #   print("File (%s) already exists." % (ofname))
  #   sys.exit(1)
  assets = ValidateAndFixAssets(dir)
  assets.scan()
  # print(assets._linked)
