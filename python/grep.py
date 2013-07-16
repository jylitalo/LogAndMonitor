import sys
import glob

if __name__ == '__main__':
    if len(sys.argv) < 3: print "Usage: grep text_pattern filename_pattern"
    text = sys.argv[1]
    fnames = sys.argv[2]
    for fname in glob.glob(fnames):
        f = open(fname,"r")
        line_number = 0
        for line in f:
            line_number += 1
            if text in line: print "%s (%d): %s" % (fname,line_number,line),
        f.close()
