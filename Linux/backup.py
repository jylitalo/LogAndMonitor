#!/usr/bin/python

import os
import sys
import time

if __name__ == '__main__':
    debug = 1
    verbose = 0
    dirs = "/bin /boot /etc /home /lib* /m* /opt /root /s* /tmp /usr /var"
    newdir = "/backup/" + time.strftime('%Y-week-%W')
    if os.access(newdir, os.F_OK):
        newdir = "/backup/" + time.strftime('%Y-%m-%d')
        if os.access(newdir, os.F_OK):
            print newdir + " already exists. Doing exit."
            sys.exit(1)
    args = ["-aH"]
    if verbose: args.append("-v")
    else: args.append("-q")
    if os.access("/backup/latest",os.R_OK):
        args.append("--link-dest=/backup/latest")
    cmdline = "/usr/bin/rsync %s %s %s" % (" ".join(args),dirs,newdir)
    if debug: print "### " + cmdline
    os.system(cmdline)
    if os.access("/backup/latest",os.F_OK):
        os.unlink("/backup/latest")
    os.symlink(newdir,"/backup/latest")
    sys.exit(0)
