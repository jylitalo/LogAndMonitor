#!/usr/bin/python

import glob
import os
import sys
import exifdump

class LensAnalysesOnOctopress(object):
  def process_file(self,fname):
    """ 
      Check if _fname_ has EXIF information with focal length that was used 
      in camera, when photo was taken.
      Return None, if focal length was not found
      Return focal length as string with "mm" suffix, if focal length was found.
    """
    fl = None
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
          if stag == "FocalLength":  
            fl = values[0].num
            break
      if exif_off and not fl:
        IFD = T.dump_IFD(exif_off)
        for (tag,type,values) in IFD:
          if tag in exifdump.EXIF_TAGS:
            stag = exifdump.EXIF_TAGS[tag]
            if stag == "FocalLength":  
              fl = values[0].num
              break
    f.close()
    if fl: return str(fl) + "mm"
    else: return None

  def map_filename(self,fname):
    """ 
      Map filename in blog post to filename into original image with 
      EXIF information. 
    """
    return os.path.expanduser(fname.replace("/images/","~/kuvat/jpg/",1).replace('_c.jpg','.jpg'))

  def scan(self,dir):
    focal_lengths = {'missing':[]}
    for fname in glob.glob("%s%s*.markdown" % (dir,os.sep)):
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
          # print full_img_name
          assert os.access(full_img_name, os.R_OK), "Unable to read img_file (%s) from %s" % (img_name,fname)
          fl = self.process_file(full_img_name)
          break
      f.close()
      if not fl: focal_lengths['missing'].append((url_name,title))
      elif fl in focal_lengths: focal_lengths[fl].append((url_name,title))
      else: focal_lengths[fl] = [(url_name,title)]
    return focal_lengths
    
if __name__ == '__main__':
  dir = sys.argv[1]
  ofname = sys.argv[2]
  if os.access(ofname, os.F_OK):
    print("File (%s) already exists." % (ofname))
    sys.exit(1)
  focal_lengths = LensAnalysesOnOctopress().scan(dir)
  """ create report from dictionary """
  lens_name = {
      "missing" : "Not available",
      "12mm" : "Olympus M.Zuiko 12mm f/2",
      "25mm" : "Panasonic Leica DG Summilux 25mm f/1.4",
      "60mm" : "Olympus M.Zuiko 60mm f/2.8 Macro"
      }
  k = lens_name.keys()
  k.sort()
  f = open(ofname,"w")
  for fl in k:
    f.write("<div><b>%s (%d)</b><br />\n" % (lens_name[fl],len(focal_lengths[fl])))
    for url,name in focal_lengths[fl]:
      f.write('<a href="%s">%s</a><br />\n' % (url,name))
    f.write('</div>\n')
  f.close()
