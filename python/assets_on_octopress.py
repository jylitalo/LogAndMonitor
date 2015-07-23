#!/usr/bin/python

#
# doctest requires MiniMock
# in Mac OS X: sudo easy_install MiniMock
#
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
        >>> Octopress.find_source_dir("/tmp/octo/source/by-lens")
        '/tmp/octo/source'
        >>> Octopress.find_source_dir("/tmp/octo/source")
        '/tmp/octo/source'
        >>> Octopress.find_source_dir("/tmp/jekyll/_posts")
        '/tmp/jekyll'
        >>> Octopress.find_source_dir("/tmp/jekyll/_site")
        '/tmp/jekyll'
        >>> Octopress.find_source_dir("/bound/to/fail")
        Traceback (most recent call last):
        ...
        AssertionError: unable to determine source directory from /bound/to/fail
        """
        # Octopress
        if dir.endswith("/source"): return dir
        if dir.endswith("/source/_posts"): return dir[:dir.rfind('/')]
        if os.access(dir + "/config.rg", os.R_OK) and os.access(dir + "/source",os.F_OK):
            return dir + "/source"
        if "/source/" in dir: return dir[:dir.rfind('/source/')+len('/source')]
        # Jekyll
        if dir.endswith("/_posts"): return dir[:dir.rfind('/')]
        if dir.endswith("/_site"): return dir[:dir.rfind('/')]
        if os.access(dir + "/_posts", os.R_OK): return dir
        raise AssertionError("unable to determine source directory from " + dir)

    @staticmethod
    def head(datetime,layout,title):
        if ':' in title: title = "'%s'" % (title)
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
        self._url_names = {}
        self._slides_in = []
    # end of __init__(self)

    @property
    def dir(self): return self._dir

    @dir.setter
    def dir(self, dname):
        """
        >>> a = AssetsFinder()
        >>> a.dir("invalid")
        Traceback (most recent call last):
        ...
        AssertionError: Source Directory (invalid) is missing sub-directories: _posts, _images, assets
        >>> from minimock import mock
        >>> mock('os.path.isdir',returns=True)
        >>> a.dir("valid")
        >>> self._dir
        valid
        """
        errors = []
        for key in ["_posts","_images"]:
            if not os.path.isdir("%s/%s" % (dname,key)): errors.append(key)
        if errors:
            raise AssertionError("Source directory (%s) is missing sub-directories: %s" % (dir,", ".join(errors)))
        self._dir = dname
    # end of dif(self, dname)

    def _scan_tree(self,subdir):
        ret = []
        ignore = len(self.dir)
        for root,dirnames,fnames in os.walk(self.dir + subdir):
            root = root[ignore:]
            fnames = [os.path.join(root,fn) for fn in fnames]
            fnames = [fn for fn in fnames if not self._ignore(fn) and self._validate_found(fn)]
            ret.extend(fnames)
        return ret
    # enf of _scan_tree(self,subdir)

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
        if fname.startswith("/_images/") and fname.count('/') == 2: return True
        return False
    # end of _ignore(fname)

    def _find_markdown_files(self):
        """
        >>> a = AssetsFinder()
        >>> ret1 = ('.',[],['index.markdown','1970-01-01-valid.markdown'])
        >>> ret2 = ('abc',[],['.#foo.markdown#','abc.markdown','abc.markdown~'])
        >>> from minimock import mock
        >>> mock('os.walk',returns=[ret1,ret2])
        >>> a._find_markdown_files()
        Called os.walk(None, followlinks=True)
        ['./index.markdown', './1970-01-01-valid.markdown', 'abc/abc.markdown']
        """
        ret = []
        for root,dirnames,fnames in os.walk(self.dir, followlinks=True):
            flist = fnmatch.filter(fnames,"[0-9a-z]*.markdown")
            ret.extend([os.path.join(root,fn) for fn in flist])
        return ret
    # end of _find_markdown_files(self)

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
    # end of get_url(fname)

    def scan(self):
        self.dir = self.find_source_dir()
        print("### using %s as root directory" % (self.dir))
        fnames = self._find_markdown_files()
        if not fnames:
            raise AssertionError("Unable to find any markdown files from " + self.dir)
        print("### processing %d markdown files" % (len(fnames)))
        for fname in fnames:
            url_name = self.get_url(fname)
            if url_name in self._url_names:
                raise AssertionError("Found duplicate url on following files: %s, %s" % (self._url_names[url_name],fname))
        self._url_names[url_name] = fname
        f = open(fname)
        slides_found = False
        for line in f:
            if not slides_found and line.startswith("{% slide "):
                self._slides_in.append(fname)
                slides_found = True
            for link in self._extract_from_markdown(line):
                if link.startswith("/images/"): link = "/_images/" + link[8:]
                if link in self._linked: self._linked[link].append(url_name)
                else: self._linked[link] = [url_name]
        f.close()
    # end of scan(self)

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
        if line.startswith("{% slide "):
            link = line.split(' ')[2]
            line = "(%s_t.jpg)(%s_l.jpg)" % (link,link)
        elif line.startswith("{% gslide "):
            link = line.split(' ')[2]
            line = "(%s_t.jpg)" % (link)
        elif line.startswith("{% cover "):
            link = line.split(' ')[2]
            line = "(%s_t.jpg)(%s_c.jpg)" % (link,link)

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
    # end of _extract_from_markdown(line)

    def _validate_found(self, fname): return True
    def _validate_waste(self,fname): print("WASTE: '%s'" % (fname))
    def _validate_missing(self, fname):
        print("MISSING: '%s' (%s)" % (fname, ", ".join(self._linked[fname])))

    def validate(self):
        found = set()
        for key in ["assets","_images"]: found.update(self._scan_tree("/" + key + "/"))
        linked = set(self._linked.keys())
        waste = list(found - linked)
        waste.sort()
        for fname in waste: self._validate_waste(fname)
        missing = list(linked - found)
        missing.sort()
        for fname in missing:
            if "/_images/" in fname: fname = fname.replace("/images/", "/_images/")
            self._validate_missing(fname)
        if self._slides_in:
            print "!!! slide plugin used in following files:"
            for f in self._slides_in: print "!!! " + f
    # end of validate(self)

class AssetsFixer(AssetsFinder):
    def __init__(self):
        AssetsFinder.__init__(self)
        self._images_root = []
        for d in ["original_jpg","jpg"]: self._images_root.append(os.path.expanduser("~/kuvat/" + d))
        self._validate_original = True
        self._convert_missing = True
        self._original_missing = []
    # end of __init__(self)

    def _original_image(self,fname):
        # Setup
        begin_index = fname.find('/',1)
        end_index = len("_t.jpg")
        if fname[-end_index] != '_': end_index = len(".jpg")
        # Execute
        for d in self._images_root:
            pattern = "%s%s.*" % (d,fname[begin_index:-end_index])
            # print("### _original_image.pattern = " + pattern)
            original_fname = glob.glob(pattern)
            if original_fname: return original_fname[0]
            original_fname = glob.glob(pattern.replace('/IMG_','/img_'))
            if original_fname: return original_fname[0]
        return None
    # end of _original_image(self, fname)

    def _validate_found(self,fname):
        # Setup
        if fname == "/_images/2014/03/P3260000_t.jpg": return False
        if not self._validate_original: return True
        original_fname = self._original_image(fname)
        if not original_fname: return False
        # Execute
        full_fname = self.dir + fname
        original_mtime = os.stat(original_fname)[stat.ST_MTIME]
        full_mtime = os.stat(full_fname)[stat.ST_MTIME]
        if original_mtime < full_mtime: return True
        print("unlink %s (%d vs. %d)" % (full_fname,original_mtime,full_mtime))
        os.unlink(full_fname)
        return False
    # end of _validate_found(self, fname)

    def _validate_waste(self,fname):
        print("unlinking %s%s (validate waste)" % (self.dir,fname))
        os.unlink("%s%s" % (self.dir,fname))

    def _resize_image(self,source_name,dest_name,resolution):
        cmdline = "convert -resize %s %s %s" % (resolution,source_name,dest_name)
        print("### " + cmdline)
        os.system(cmdline)

    def _validate_missing(self,fname):
        # Setup
        if fname == "/_images/2014/03/P3260000_t.jpg":
            return
        if not self._convert_missing:
            AssetsFinder._validate_missing(self,fname)
            return
        original_fname = self._original_image(fname)
        if not original_fname:
            self._original_missing.append((fname,", ".join(self._linked[fname])))
            return
        # Execute
        full_fname = self.dir + fname
        dname = os.path.dirname(full_fname)
        if not os.access(dname,os.F_OK): os.makedirs(dname)
        assert os.access(dname,os.W_OK), "need write access to " + dname
        print("### images for: " + ",".join(self._linked[fname]))
        if fname.endswith("_t.jpg"):
            cmdline = "convert -thumbnail 150x150^ -gravity center -extent 150x150 %s %s" % (original_fname,full_fname)
            print("### " + cmdline)
            os.system(cmdline)
        elif fname.endswith("_c.jpg"):
            self._resize_image(original_fname,full_fname,"750x750")
        elif fname.endswith("_l.jpg"):
            self._resize_image(original_fname,full_fname,"1280x800")
        else:
            print("### unknown suffix on " + fname)
    # end of _validate_missing(self, fname)

    def validate(self):
        AssetsFinder.validate(self)
        if self._original_missing:
            print "!!! Original image missing for:"
            for fname,references in self._original_missing:
                print("!!! %s references: %s" % (fname,references))
    # end of validate(self)

if __name__ == '__main__':
    assets = AssetsFixer()
    assets.scan()
    assets.validate()
