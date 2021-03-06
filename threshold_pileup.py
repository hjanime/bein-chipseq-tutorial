#!/bin/env python
"""
threshold_pileup.py
by Fred Ross, <fred.ross@epfl.ch>
May 19, 2011

Takes a threshold, a mean fragment size, and a CSV of
chromosome,position,pileup and finds regions which are above the
threshold and sufficiently wide to be hits.  Then it uses the mean fragment size to estimate the position of the hit.  Outputs them as a CSV of chromosome,position.
"""
import os
import sys
import csv
import getopt

usage = """Usage: threshold_pileup.py [-h] [-o output.txt] threshold frag_len pileup.txt

-h             Print this message and exit
-o output.txt  Write output to output.txt (default: stdout)
threshold      Positive integer specifying the threshold
frag_len       Mean fragment size
pileup.txt     CSV file of the form chromosome,position,pileup
"""

class Usage(Exception):
    def __init__(self,  msg):
        self.msg = msg

def read_pileup(lines):
    pileup = {}
    last_chromosome = None
    last_position = None
    for chromosome,position,count in lines:
        position = int(position)
        count = int(count)
        if last_chromosome != chromosome:
            if not(pileup.has_key(chromosome)):
                pileup[chromosome] = []
            last_position = -1
            last_chromosome = chromosome
        if position != last_position + 1:
            raise ValueError("Positions are not sequential in pileup file.")
        last_position += 1
        pileup[chromosome].append(count)
    return pileup

def smooth(seq):
    seq2 = []
    seq2.append( (seq[0]+seq[1])/2.0 )
    for i in range(1, len(seq)-1):
        seq2.append( (seq[i-1]+seq[i]+seq[i+1])/3.0 )
    seq2.append( (seq[-1]+seq[-2])/2.0 )
    return seq2

def find_regions(seq, threshold, min_width):
    i = 0
    regions = []
    while i < len(seq):
        if seq[i] <= threshold:
            i += 1
        else:
            j = i
            while j < len(seq) and seq[j] > threshold:
                j += 1
            if j-i > min_width:
                regions.append((i,j))
            i = j
    return regions

def main(argv=None):
    output = sys.stdout
    if argv is None:
        argv = sys.argv[1:]
    try:
        try:
            opts, args = getopt.getopt(argv, "ho:", ["help"])
        except getopt.error, msg:
            raise Usage(msg)
        for o, a in opts:
            if o in ("-h", "--help"):
                print __doc__
                print usage
                sys.exit(0)
            elif o in ("-o",):
                if os.path.exists(a):
                    raise Usage("Output file %s already exists" % a)
                else:
                    output = open(a, 'w')
            else:
                raise Usage("Unhandled option: " + o)

        if len(args) != 3:
            raise Usage("threshold_pileup.py takes exactly three arguments.")

        [threshold, frag_len, pileup] = args

        if not(os.path.exists(pileup)):
            raise Usage("Input file does not exist.")

        try:
            threshold = int(threshold)
        except ValueError, v:
            raise Usage("Threshold must be a positive integer")

        try:
            frag_len = int(frag_len)
        except ValueError, v:
            raise Usage("Min_width must be a positive integer")

        if threshold < 1:
            raise Usage("Threshold must be a positive integer")
        if frag_len < 1:
            raise Usage("Threshold must be a positive integer")

        with open(pileup) as f:
            r = csv.reader(f)
            p = read_pileup(r)

        min_width = (frag_len/2.0) * 0.7

        output_writer = csv.writer(output)
        keys = p.keys()
        keys.sort()
        for k in keys:
            p[k] = smooth(p[k])
            for start,end in find_regions(p[k], threshold, min_width):
                pos = (end-start)/2.0 + start + frag_len/2.0
                output_writer.writerow((k, pos))
        
        output.close()
        sys.exit(0)
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, usage
        return 2
    

if __name__ == '__main__':
    sys.exit(main())
