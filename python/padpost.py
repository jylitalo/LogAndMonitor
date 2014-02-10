#!/usr/local/bin/python

import glob
import os
import sys
import datetime

import assets_on_octopress
import lens_analyses_on_octopress

class PADpost(assets_on_octopress.AssetsFixer):
  def __init__(self, start_at, end_at):
    assets_on_octopress.AssetsFixer.__init__(self)
    self.__start_at = start_at
    self.__end_at = end_at
    self.exif = lens_analyses_on_octopress.LensFromEXIF()

  def _post_name(self,taken_date,subject):
    """
    +++ PADpost._post_name("foo/source","2013-11-11","Foo bar")
    'foo/source/_posts/2013-11-11-foo-bar.markdown'
    """
    dir = self.find_source_dir()
    fname = subject.replace(' ','-').replace(':','').lower()
    fname = "%s/_posts/%s-%s.markdown" % (dir,taken_date,fname)
    return fname

  def post(self,img_name,subject):
    taken_date, lens = self.exif.process_file(img_name)

    days_done = self._days(self.__start_at,taken_date)
    days_total = self._days(self.__start_at,self.__end_at)
    title = "%s (%d/%d)" % (subject,days_done,days_total)

    f = open(self._post_name(taken_date,subject),"w")
    f.write(self.head(taken_date + " 12:00:00",'post',title))

    url = self._img_url(taken_date,img_name)
    f.write('''
![%s](%s)
<!--more-->
%s
''' % (subject,url,lens))
    f.close()

  @staticmethod
  def _days(start_at, end_at):
    """
    >>> PADpost._days("2013-01-01","2013-01-31")
    31
    >>> PADpost._days("2013-01-01","2013-12-31")
    365
    >>> PADpost._days("2013-01-01","2014-12-31")
    730
    """
    start_t = datetime.datetime.strptime(start_at,"%Y-%m-%d")
    end_t = datetime.datetime.strptime(end_at,"%Y-%m-%d")
    return (end_t-start_t).days+1

  @staticmethod
  def _img_url(taken_date, img_name):
    """
    >>> PADpost._img_url("2013-11-11","~/kuvat/jpg/2013/11/PB123456.jpg")
    '/images/2013/11/PB123456_c.jpg'
    """
    year,month = taken_date[:4],taken_date[5:7]
    fname = img_name[img_name.rfind('/'):img_name.rfind('.')]
    return "/images/%s/%s%s_c.jpg" % (year,month,fname)
 
if __name__ == '__main__':
  img_fname = sys.argv[1]
  subject = sys.argv[2]

  pad = PADpost("2013-01-01","2014-12-31")
  pad.post(img_fname,subject)
  pad.scan()
  pad.validate()
