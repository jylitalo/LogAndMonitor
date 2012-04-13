#!/usr/bin/python

import os
import sys
import time
import ConfigParser

if __name__ == '__main__':
    debug = 1
    verbose = 0
    if debug > 1 or verbose: print "### " + time.ctime()
    ###
    # rsync
    ###
    dirs = "/bin /boot /etc /home /lib* /m* /opt /root /s* /tmp /usr /var"
    newdir = "/backup/" + time.strftime('%Y-week-%W')
    if os.access(newdir, os.F_OK):
        newdir = "/backup/" + time.strftime('%Y-%m-%d')
        if os.access(newdir, os.F_OK):
            print newdir + " already exists. Doing exit."
            sys.exit(1)

    # arguments for rsync
    args = ["-aH --exclude=/var/spool/pnp4nagios"]
    if verbose: args.append("-v")
    else: args.append("-q")
    if os.access("/backup/latest",os.R_OK):
        args.append("--link-dest=/backup/latest")

    # execution
    cmdline = "/usr/bin/rsync %s %s %s" % (" ".join(args),dirs,newdir)
    if debug > 1: print "### " + cmdline
    os.system(cmdline)
    if debug > 1 or verbose: print "### " + time.ctime()

    # update /backup/latest to latest rsync
    if os.access("/backup/latest",os.F_OK): os.unlink("/backup/latest")
    os.symlink(newdir,"/backup/latest")

    ###
    # MySQL
    ###
    fname = "/etc/backup.cf"
    if os.access(fname, os.R_OK):
        # Configuation file
        if debug > 1: print "### mysqldump"
        cf = ConfigParser.ConfigParser()
        cf.read(fname)
        username = cf.get("mysql","username")
        password = cf.get("mysql","password")
        email = None
        if cf.has_option("mysql","email"): email = cf.get("mysql","email")

        # arguments for mysqldump
        newdump = "/backup/mysql/mysql-" + time.strftime('%d')
        if os.access(newdump,os.F_OK): os.unlink(newdump)
        args = ["-u %s -p'%s' --all-databases -r%s" % (username,password,newdump)]
        if verbose: args.append("-v")

        # execution
        cmdline = "mysqldump " + " ".join(args)
        if debug > 1: print "### " + cmdline
        os.system(cmdline)

        # post-proessing (email (if needed) + gzip)
        if debug > 1 or verbose: print "### " + time.ctime()
        if email:
            os.system('/bin/mail %s -s "%s.sql" < %s' % (email,newdump,newdump))
        if os.access(newdump + ".gz", os.W_OK): os.unlink(newdump + ".gz")
        os.system("/usr/bin/gzip -9 " + newdump)
        if debug > 1 or verbose: print "### " + time.ctime()
    elif debug:
        print "### no configuration file for mysqldump"
    sys.exit(0)
