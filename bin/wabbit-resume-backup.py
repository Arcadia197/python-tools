#!/usr/bin/env python3
import sys, os
sys.path.append(os.path.join(os.path.split(__file__)[0], ".."))
import inifile_tools

print("----------------------------------------")
print(" wabbit: resume simulation")
print(" wabbit-resume-backup.py [inifile] ")
print(" wabbit-resume-backup.py suzuki.ini")
print("----------------------------------------")

if len(sys.argv) < 2:
    print("ERROR: Did you forget to provide any inifile that I should look at?")
    sys.exit(1)

inifile = sys.argv[1]
if not os.path.isfile(inifile):
    print("ERROR: I did not find any inifile :(")
else:
    print( "inifile is " + inifile )
    inifile_tools.prepare_resuming_backup( inifile )