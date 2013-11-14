#!/usr/bin/python

import fnmatch
import glob
import os
import stat
import sys

class AssetsFinder(object):
  def __init__(self,dir):
    # Setup
    errors = []
    for key in ["_posts","images","assets"]:
      if not os.path.isdir("%s/%s" % (dir,key)): errors.append(key)
    if errors:
      print("""Invalid directory for Octopress source.
%s doesn't have following subdirectories: %s
Doing exit.""" % (dir,", ".join(errors)))
      sys.exit(2)
    # Execute
    self._dir = dir
    self.debug = False
    self._found = []
    self._linked = {}

  def _extract_from_markdown(self, line, name):
    for field in line.split("(/")[1:]:
      field = "/" + field[:field.find(')')]
      if ' "' in field: field = field[:field.find(' "')]
      if field.startswith("/images/") or field.startswith("/assets/"):
         if field in self._linked: self._linked[field].append(name)
         else: self._linked[field] = [name]
    for c in [' ','"']:
      for field in line.split(c + '/')[1:]:
        field = "/" + field[:field.find(c,1)]
        if field.startswith("/images/") or field.startswith("/assets/"):
           if field in self._linked: self._linked[field].append(name)
           else: self._linked[field] = [name]

  def _scan_tree(self,subdir):
    ret = []
    ignore = len(self._dir)
    for root,dirnames,filenames in os.walk(self._dir + subdir):
      for filename in filenames:
        fname = os.path.join(root, filename)[ignore:]
        self._validate_found(fname)
    return ret

  def scan(self):
    begin_index = len("yyyy-mm-dd-")
    end_index = len(".markdown")
    markdown_files = []
    for root,dirnames,filenames in os.walk(self._dir):
      for fname in fnmatch.filter(filenames,"*.markdown"):
        markdown_files.append(os.path.join(root,fname))
    if not markdown_files:
      print("### Unable to find any markdown files from " + self._dir)
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
            self._extract_from_markdown(line,url_name)
          elif '/images/' in line or '/assets/' in line:
            self._extract_from_markdown(line,url_name)
      f.close()
    print("### found %d links" % (len(self._linked)))
    self._scan_tree("/assets/")
    print("### found after /assets/ is %d"% (len(self._found)))
    self._scan_tree("/images/")
    print("### found after /images/ is %d"% (len(self._found)))

  def _validate_found(self, fname):
    if not self._ignore(fname): self._found.append(fname)

  def _validate_waste(self,fname): print("WASTE: '%s'" % (fname))
  def _validate_missing(self, fname): print("MISSING: '%s' (%s)" % (fname, ", ".join(self._linked[fname])))

  def _ignore(self, fname):
    if fname.endswith("/.DS_Store"): return True
    if fname.startswith("/assets/jwplayer"): return True
    elif fname.startswith("/images/") and fname.count('/') == 2: return True
    return False

  def remove_matches(self):
    # print("found_images = %d" % (len(self._found_images)))
    if self._found:
      self._found.sort()
      for fname in self._found:
        if fname in self._linked: del self._linked[fname]
        else: self._validate_waste(fname)
    if self._linked: 
      linked_keys = self._linked.keys()
      linked_keys.sort()
      for fname in linked_keys: self._validate_missing(fname)

class AssetsFixer(AssetsFinder):
  def __init__(self,dir):
    AssetsFinder.__init__(self,dir)
    self._images_root = os.path.expanduser("~/kuvat/original_jpg")
    self._validate_original = True
    self._convert_missing = True

  def _original_image(self,fname):
    # Setup
    begin_index = fname.find('/',1)
    end_index = len("_t.jpg")
    if fname[-end_index] != '_': end_index = len(".jpg")
    # Execute
    pattern = "%s%s.*" % (self._images_root,fname[begin_index:-end_index])
    original_fname = glob.glob(pattern)
    if original_fname: return original_fname[0]
    original_fname = glob.glob(pattern.replace('/IMG_','/img_'))
    if original_fname: return original_fname[0]
    return None

  def _validate_found(self,fname):
    # Setup
    if self._ignore(fname): return
    if not self._validate_original:
      self._found.append(fname)
      return
    # Execute
    original_fname = self._original_image(fname)
    if original_fname:
      full_fname = self._dir + fname
      original_mtime = os.stat(original_fname)[stat.ST_MTIME]
      full_mtime = os.stat(full_fname)[stat.ST_MTIME]
      if original_mtime >= full_mtime:
        print("unlink %s (%d vs. %d)" % (full_fname,original_mtime,full_mtime))
        os.unlink(full_fname)
      else: self._found.append(fname)
    else: 
      print("### unable to find original file for " + fname)

  def _validate_waste(self,fname):
    print("unlinking %s%s (validate waste)" % (self._dir,fname))
    os.unlink("%s%s" % (self._dir,fname))

  def _resize_image(self,source_name,dest_name,resolution):
    cmdline = "convert -resize %s %s %s" % (resolution,source_name,dest_name)
    print("### " + cmdline)
    os.system(cmdline)

  def _validate_missing(self,fname):
    # Setup
    if not self._convert_missing: 
      AssetsFinder._validate_missing(self,fname)
      return
    # Execute
    original_fname = self._original_image(fname)
    if not original_fname:
      print("### unable to find original_image for %s (references: %s)" % (fname,", ".join(self._linked[fname])))
    fname = self._dir + fname
    dname = os.path.dirname(fname)
    if not os.access(dname,os.F_OK): os.mkdir(dname)
    if fname.endswith("_t.jpg"):
      cmdline = "convert -thumbnail 150x150^ -gravity center -extent 150x150 %s %s" % (original_fname,fname)
      print("### " + cmdline)
      os.system(cmdline)
    elif fname.endswith("_c.jpg"):
      self._resize_image(original_fname,fname,"750x750")
    elif fname.endswith("_l.jpg"):
      self._resize_image(original_fname,fname,"1024x750")


if __name__ == '__main__':
  if len(sys.argv) < 2: 
    print("Usage: assets_on_octopress.py [dir]")
    sys.exit(4)
  dir = sys.argv[1]
  # ofname = sys.argv[2]
  # if os.access(ofname, os.F_OK):
  #   print("File (%s) already exists." % (ofname))
  #   sys.exit(1)
  assets = AssetsFixer(dir)
  assets.scan()
  assets.remove_matches()
