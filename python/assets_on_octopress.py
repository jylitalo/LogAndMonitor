#!/usr/bin/python

import fnmatch
import glob
import os
import stat
import sys

class AssetsFinder(object):
  def __init__(self):
    self._dir = None
    self._found = []
    self._linked = {}

  @property
  def dir(self): return self._dir

  @dir.setter
  def dir(self, dname):
    errors = []
    for key in ["_posts","images","assets"]:
      if not os.path.isdir("%s/%s" % (dname,key)): errors.append(key)
    if errors:
      print("""Invalid directory for Octopress source.
%s doesn't have following subdirectories: %s
Doing exit.""" % (dir,", ".join(errors)))
      sys.exit(2)
    self._dir = dname

  @staticmethod
  def _extract_from_markdown(line):
    """
      >>> AssetsFinder._extract_from_markdown("foobar")
      []
      >>> AssetsFinder._extract_from_markdown('[foobar](/images/link.jpg)')
      ['/images/link.jpg']
      >>> AssetsFinder._extract_from_markdown('[foobar](/images/link.jpg "foobar")')
      ['/images/link.jpg']
      >>> AssetsFinder._extract_from_markdown('{% img /images/something.jpg "foobar"}')
      ['/images/something.jpg']
    """
    links = []
    for key in ["images","assets"]:
      for field in line.split("(/" + key)[1:]:
        field = "/%s%s" % (key,field[:field.find(')')])
        if ' "' in field: field = field[:field.find(' "')]
        links.append(field)
      for c in [' ','"',"'"]:
        for field in line.split("%s/%s" % (c,key))[1:]:
          field = "/" + key + field[:field.find(c,1)]
          links.append(field)
    return links

  def _scan_tree(self,subdir):
    ret = []
    ignore = len(self.dir)
    for root,dirnames,filenames in os.walk(self.dir + subdir):
      for filename in filenames:
        fname = os.path.join(root, filename)[ignore:]
        if not self._ignore(fname): self._validate_found(fname)
    return ret

  def _find_markdown_files(self):
    ret = []
    for root,dirnames,fnames in os.walk(self.dir):
      flist = [os.path.join(root,fn) for fn in fnmatch.filter(fnames,"*.markdown")]
      ret.extend(flist)
    if not ret:
      print("### Unable to find any markdown files from " + self.dir)
      sys.exit(1)
    else:
      print("### processing %d markdown files" % (len(ret)))
    return ret

  def scan(self,dir):
    self.dir = dir
    begin_index = len("yyyy-mm-dd-")
    end_index = len(".markdown")

    for fname in self._find_markdown_files():
      f = open(fname)
      url_name = "/" + os.path.basename(fname)[begin_index:-end_index] + "/"
      for line in f:
        for link in AssetsFinder._extract_from_markdown(line):
          if link in self._linked: self._linked[link].append(url_name)
          else: self._linked[link] = [url_name]
      f.close()
    for key in ["assets","images"]: self._scan_tree("/" + key + "/")

  def _validate_found(self, fname): self._found.append(fname)
  def _validate_waste(self,fname): print("WASTE: '%s'" % (fname))
  def _validate_missing(self, fname): print("MISSING: '%s' (%s)" % (fname, ", ".join(self._linked[fname])))

  def _ignore(self, fname):
    """
      >>> AssetsFinder()._ignore("/foobar/.DS_Store")
      True
      >>> AssetsFinder()._ignore("/assets/jwplayer/foobar")
      True
      >>> AssetsFinder()._ignore("/images/foobar.jpg")
      True
      >>> AssetsFinder()._ignore("/images/2013/11/IMG_1234_t.jpg")
      False
    """
    if fname.endswith(".DS_Store"): return True
    if fname.startswith("/assets/jwplayer"): return True
    elif fname.startswith("/images/") and fname.count('/') == 2: return True
    return False

  def validate(self):
    # print("found_images = %d" % (len(self._found_images)))
    self._found.sort()
    for fname in self._found:
      if fname in self._linked: del self._linked[fname]
      else: self._validate_waste(fname)
    linked_keys = self._linked.keys()
    linked_keys.sort()
    for fname in linked_keys: self._validate_missing(fname)

class AssetsFixer(AssetsFinder):
  def __init__(self):
    AssetsFinder.__init__(self)
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
    if not self._validate_original:
      self._found.append(fname)
      return True
    original_fname = self._original_image(fname)
    if not original_fname:
      print("### unable to find original file for " + fname)
      return False
    # Execute
    full_fname = self.dir + fname
    original_mtime = os.stat(original_fname)[stat.ST_MTIME]
    full_mtime = os.stat(full_fname)[stat.ST_MTIME]
    if original_mtime >= full_mtime:
      print("unlink %s (%d vs. %d)" % (full_fname,original_mtime,full_mtime))
      os.unlink(full_fname)
      return False
    else: 
      self._found.append(fname)
      return True

  def _validate_waste(self,fname):
    print("unlinking %s%s (validate waste)" % (self.dir,fname))
    os.unlink("%s%s" % (self.dir,fname))

  def _resize_image(self,source_name,dest_name,resolution):
    cmdline = "convert -resize %s %s %s" % (resolution,source_name,dest_name)
    print("### " + cmdline)
    os.system(cmdline)

  def _validate_missing(self,fname):
    # Setup
    if not self._convert_missing: 
      AssetsFinder._validate_missing(self,fname)
      return
    original_fname = self._original_image(fname)
    if not original_fname:
      print("### unable to find original_image for %s (references: %s)" % (fname,", ".join(self._linked[fname])))
      return
    # Execute
    fname = self.dir + fname
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
  assets = AssetsFixer()
  assets.scan(dir)
  assets.validate()
