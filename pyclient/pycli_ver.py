#!/usr/bin/env python

# ------------------------------------------------------------------------
# Test client for the pyserv project. Encrypt test.

import  os, sys, getopt, signal, select, socket, time, struct
import  random, stat

sys.path.append('..')
sys.path.append('../common')
import support, pycrypt, pyservsup, pyclisup, syslog

# ------------------------------------------------------------------------
# Functions from command line

def phelp():

    print()
    print( "Usage: " + os.path.basename(sys.argv[0]) + " [options]")
    print()
    print( "Options:    -d level  - Debug level 0-10")
    print( "            -p port   - Port to use (default: 9999)")
    print( "            -v        - Verbose")
    print( "            -q        - Quiet")
    print( "            -h        - Help")
    print()
    sys.exit(0)

def pversion():
    print( os.path.basename(sys.argv[0]), "Version", support.version)
    sys.exit(0)
 
    # option, var_name, initial_val, function
optarr = \
    ["d:",  "pgdebug",  0,      None],      \
    ["p:",  "port",     9999,   None],      \
    ["v",   "verbose",  0,      None],      \
    ["q",   "quiet",    0,      None],      \
    ["t",   "test",     "x",    None],      \
    ["V",   None,       None,   pversion],  \
    ["h",   None,       None,   phelp]      \
    
conf = pyclisup.Config(optarr)

# ------------------------------------------------------------------------

if __name__ == '__main__':

    #if  sys.version_info[0] < 3:
    #    print("Needs python 3 or better.")
    #    sys.exit(1)
    #
    args = conf.comline(sys.argv[1:])
    
    if len(args) == 0:
        ip = '127.0.0.1'
    else:
        ip = args[0]
    s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        s1.connect((ip, conf.port))
    except:
        print( "Cannot connect to:", ip + ":" + str(conf.port), sys.exc_info()[1])
        sys.exit(1)

    hand = pyclisup.CliSup(s1)
    hand.verbose = conf.verbose
    hand.pgdebug = conf.pgdebug
    
    resp = hand.client("ver")
    print ("Server response:", resp)
    hand.client("quit")
    
    s1.close();
    sys.exit(0)





