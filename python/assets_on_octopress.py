#!/usr/bin/python

import fnmatch
import glob
import os
import stat
import sys

class Octopress(object):
  @staticmethod
  def find_source_dir(dir=os.getcwd()):
    """
    >>> Octopress.find_source_dir("/tmp/octo/source/_posts")
    '/tmp/octo/source'
    >>> Octopress.find_source_dir("/tmp/octo/source")
    '/tmp/octo/source'
    >>> Octopress.find_source_dir("/bound/to/fail")
    Traceback (most recent call last):
    ...
    AssertionError: unable to determine source directory from /bound/to/fail
    """
    if dir.endswith("/source"): return dir
    if dir.endswith("/source/_posts"): return dir[:dir.rfind('/')]
    if os.access(dir + "/config.rg", os.R_OK) and os.access(dir + "/source",os.F_OK): 
      return dir + "/source"
    raise AssertionError("unable to determine source directory from " + dir)

  @staticmethod
  def head(datetime,layout,title):
    return """---
date: '%s'
layout: %s
status: publish
title: %s
---
""" % (datetime,layout,title)

class AssetsFinder(Octopress):
  def __init__(self):
    self._dir = None
    self._linked = {}

  @property
  def dir(self): return self._dir

  @dir.setter
  def dir(self, dname):
    errors = []
    for key in ["_posts","images","assets"]:
      if not os.path.isdir("%s/%s" % (dname,key)): errors.append(key)
    if errors:
      raise AssertionError("Source directory (%s) is missing sub-directories: %s" % (dir,", ".join(errors)))
    self._dir = dname

  def _scan_tree(self,subdir):
    ret = []
    ignore = len(self.dir)
    for root,dirnames,fnames in os.walk(self.dir + subdir):
      root = root[ignore:]
      fnames = [os.path.join(root,fn) for fn in fnames]
      fnames = [fn for fn in fnames if not self._ignore(fn) and self._validate_found(fn)]
      ret.extend(fnames)
    return ret

  @staticmethod
  def _ignore(fname):
    """
      >>> AssetsFinder._ignore("/foobar/.DS_Store")
      True
      >>> AssetsFinder._ignore("/assets/jwplayer/foobar")
      True
      >>> AssetsFinder._ignore("/images/foobar.jpg")
      True
      >>> AssetsFinder._ignore("/_posts/.#1970-01-01-foobar.markdown")
      True
      >>> AssetsFinder._ignore("/images/2013/11/IMG_1234_t.jpg")
      False
    """
    if fname.endswith(".DS_Store"): return True
    if fname.startswith("/assets/jwplayer"): return True
    if fname.find("/.#") > -1: return True
    if fname.startswith("/images/") and fname.count('/') == 2: return True
    return False

  def _find_markdown_files(self):
    ret = []
    for root,dirnames,fnames in os.walk(self.dir):
      flist = fnmatch.filter(fnames,"[0-9]*.markdown")
      ret.extend([os.path.join(root,fn) for fn in flist])
    return ret

  @staticmethod
  def get_url(fname):
    """
    >>> AssetsFinder.get_url("foo/source/_posts/2013-11-27-foobar.markdown")
    'foobar'
    >>> AssetsFinder.get_url("foo/source/_posts/2013-11-27-foo-bar.markdown")
    'foo-bar'
    >>> AssetsFinder.get_url("foo/source/foobar/index.markdown")
    'foobar'
    >>> AssetsFinder.get_url("foo/source/foo-bar/index.markdown")
    'foo-bar'
    >>> AssetsFinder.get_url("foo/source/foobar.markdown")
    'foobar'
    >>> AssetsFinder.get_url("foo/source/foo-bar.markdown")
    'foo-bar'
    """
    end_index = len(".markdown")
    fname = fname[:-end_index]
    if "source/_posts/" in fname:
      begin_index = len("yyyy-mm-dd-")
      return os.path.basename(fname)[begin_index:]
    if fname.endswith("/index"):
      fname = fname[:-len("/index")]
      return fname[fname.rfind('/')+1:]
    else: return os.path.basename(fname)

  def scan(self):
    self.dir = self.find_source_dir()
    fnames = self._find_markdown_files()
    if not fnames:
      raise AssertionError("Unable to find any markdown files from " + self.dir)
    print("### processing %d markdown files" % (len(fnames)))
    for fname in fnames:
      url_name = self.get_url(fname)
      f = open(fname)
      for line in f:
        for link in self._extract_from_markdown(line):
          if link in self._linked: self._linked[link].append(url_name)
          else: self._linked[link] = [url_name]
      f.close()

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
      >>> AssetsFinder._extract_from_markdown('[![#48/2012: Rautatientori](/images/2012/11/IMG_0156_t.jpg "#48/2012: Rautatientori")](/images/2012/11/IMG_0156_l.jpg "#48/2012: Rautatientori")')
      ['/images/2012/11/IMG_0156_t.jpg', '/images/2012/11/IMG_0156_l.jpg']
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

  def _validate_found(self, fname): return True
  def _validate_waste(self,fname): print("WASTE: '%s'" % (fname))
  def _validate_missing(self, fname): 
    print("MISSING: '%s' (%s)" % (fname, ", ".join(self._linked[fname])))

  def validate(self):
    found = set()
    for key in ["assets","images"]: found.update(self._scan_tree("/%s/" % (key)))
    linked = set(self._linked.keys())
    waste = list(found - linked)
    waste.sort()
    for fname in waste: self._validate_waste(fname)
    missing = list(linked - found)
    missing.sort()
    for fname in missing: self._validate_missing(fname)

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
    if not self._validate_original: return True
    original_fname = self._original_image(fname)
    if not original_fname:
      print("### unable to find original file for " + fname)
      return False
    # Execute
    full_fname = self.dir + fname
    original_mtime = os.stat(original_fname)[stat.ST_MTIME]
    full_mtime = os.stat(full_fname)[stat.ST_MTIME]
    if original_mtime < full_mtime: return True
    print("unlink %s (%d vs. %d)" % (full_fname,original_mtime,full_mtime))
    os.unlink(full_fname)
    return False

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
    full_fname = self.dir + fname
    dname = os.path.dirname(full_fname)
    if not os.access(dname,os.F_OK): os.mkdir(dname)
    print("### images for: " + ",".join(self._linked[fname]))
    if fname.endswith("_t.jpg"):
      cmdline = "convert -thumbnail 150x150^ -gravity center -extent 150x150 %s %s" % (original_fname,full_fname)
      print("### " + cmdline)
      os.system(cmdline)
    elif fname.endswith("_c.jpg"):
      self._resize_image(original_fname,full_fname,"750x750")
    elif fname.endswith("_l.jpg"):
      self._resize_image(original_fname,full_fname,"1024x750")


if __name__ == '__main__':
  assets = AssetsFixer()
  assets.scan()
  assets.validate()
