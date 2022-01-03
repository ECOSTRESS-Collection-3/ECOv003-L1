#! /usr/bin/env python
#
# Short script to dump QA data. We'll improve this over time

import geocal
import h5py

version = "1.0"
usage='''Usage:
  dump_qa.py [options] <qa_file>
  dump_qa.py -h | --help
  dump_qa.py -v | --version

This reads and writes out basic QA information. We'll replace this at some
point with a full database.
Options:
  -h --help         
       Print this message

  -v --version      
       Print program version
'''

args = geocal.docopt_simple(usage, version=version)
f = h5py.File(args.qa_file, "r")
print("Orbit number:        %s" % f["StandardMetadata/StartOrbitNumber"][()])
print("Corection performed: %s" % f["L1GEOMetadata/OrbitCorrectionPerformed"][()])
slist = f["Accuracy Estimate/Scenes"][:]
acc = f["Accuracy Estimate/Final Accuracy"][:]
lfrac = f["Average Metadata"][:,1]
ntie = f["Tiepoint/Tiepoint Count"][:,2]
print("Scene   Land Fraction Num Tiepoint Accuracy Estimate")
print("------  ------------- ------------ -----------------")
for i in range(slist.shape[0]):
    print("{:s}        {:>5.1f}          {:>0d}          {:>03.1f}".format(slist[i].decode('utf-8'), lfrac[i], ntie[i], acc[i]))
