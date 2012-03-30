#!/usr/bin/python

import os
import sys
import time
import ConfigParser

if __name__ == '__main__':
    debug = 1
    verbose = 0
    if debug or verbose: print "### " + time.ctime()
    dirs = "/bin /boot /etc /home /lib* /m* /opt /root /s* /tmp /usr /var"
    newdir = "/backup/" + time.strftime('%Y-week-%W')
    if os.access(newdir, os.F_OK):
        newdir = "/backup/" + time.strftime('%Y-%m-%d')
        if os.access(newdir, os.F_OK):
            print newdir + " already exists. Doing exit."
            sys.exit(1)

    args = ["-aH --exclude=/var/spool/pnp4nagios"]
    if verbose: args.append("-v")
    else: args.append("-q")
    if os.access("/backup/latest",os.R_OK):
        args.append("--link-dest=/backup/latest")
    cmdline = "/usr/bin/rsync %s %s %s" % (" ".join(args),dirs,newdir)
    if debug: print "### " + cmdline
    os.system(cmdline)
    if debug or verbose: print "### " + time.ctime()

    fname = "/etc/backup.cf"
    if os.access(fname, os.R_OK):
        if debug: print "### mysqldump"
        cf = ConfigParser.ConfigParser()
        cf.read(fname)
        username = cf.get("mysql","username")
        password = cf.get("mysql","password")
        newdump = "/backup/mysql/mysql-" + time.strftime('%d')
        if os.access(newdump,os.F_OK): os.unlink(newdump)
        args = ["-u " + username,"-p'%s'" % (password),"--all-databases","-r" + newdump]
        if verbose: args.append("-v")
        cmdline = "mysqldump " + " ".join(args)
        os.system(cmdline)
        if debug or verbose: print "### " + time.ctime()
    elif debug:
        print "### no configuration file for mysqldump"

    if os.access("/backup/latest",os.F_OK):
        os.unlink("/backup/latest")
    os.symlink(newdir,"/backup/latest")
    sys.exit(0)
