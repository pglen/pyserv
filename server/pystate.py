#!/usr/bin/env python

from __future__ import print_function

from Crypto.Hash import SHA512
import os, sys, getopt, signal, select, string, time, stat, base64

#sys.path.append('..')

sys.path.append('../bluepy')
import bluepy

sys.path.append('../common')
import support, pyservsup, pyclisup, crysupp, pysyslog
import pypacker, pywrap

from pysfunc import *

# Ping pong state machine

# 1.) States

initial     = 0
auth_akey   = 1
auth_sess   = 2
auth_user   = 3
auth_key    = 4
auth_pass   = 5
in_idle     = 6
got_fname   = 7
in_trans    = 8
got_file    = 9

# The commands in this state are allowed always
all_in       = 100

# The commands in this state are allowed in all states after auth
auth_in      = 110

# The commands in this state do not set new state
none_in      = 120

# ------------------------------------------------------------------------
# Also stop timeouts

def get_exit_func(self, strx):
    #print( "get_exit_func", strx)
    self.resp.datahandler.putdata("OK Bye", self.resp.ekey)
    #self.resp.datahandler.par.shutdown(socket.SHUT_RDWR)

    # Cancel **after** sending bye
    if self.resp.datahandler.tout:
        self.resp.datahandler.tout.cancel()
    return True

def get_tout_func(self, strx):

    tout = self.resp.datahandler.timeout
    if len(strx) > 1:
        tout = int(strx[1])
        self.resp.datahandler.timeout = tout

    if self.resp.datahandler.tout:
        self.resp.datahandler.tout.cancel()

    self.resp.datahandler.putdata("OK timeout set to " + str(tout), self.resp.ekey)
    return

# ------------------------------------------------------------------------
# Help stings

user_help  = "Usage: user logon_name"
akey_help  = "Usage: akey -- get asymmetric key"
pass_help  = "Usage: pass logon_pass"
file_help  = "Usage: file fname -- Specify name for upload"
fget_help  = "Usage: fget fname -- Download (get) file"
uadd_help  = "Usage: uadd user_name user_pass -- Create new user"
kadd_help  = "Usage: kadd key_name key_val -- Add new encryption key"
uini_help  = "Usage: uini user_name user_pass -- Create initial user. "\
                "Must be from local net."
kini_help  = "Usage: kini key_name key_pass -- Create initial key. " \
                "Must be from local net."
udel_help  = "Usage: udel user_name user_pass -- Delete user"
data_help  = "Usage: data datalen -- Specify length of file to follow"
vers_help  = "Usage: ver -- Get protocol version. alias: vers"
hello_help = "Usage: hello -- Say Hello - test connectivity."
quit_help  = "Usage: quit -- Terminate connection. alias: exit"
help_help  = "Usage: help [command] -- Offer help on command"
lsls_help  = "Usage: ls [dir] -- List files in dir"
lsld_help  = "Usage: lsd [dir] -- List dirs in dir"
cdcd_help  = "Usage: cd dir -- Change to dir. Capped to server root"
pwdd_help  = "Usage: pwd -- Show current dir"
stat_help  = "Usage: stat fname  -- Get file stat. Field list:\n"\
"   1.  ST_MODE Inode protection mode.\n"\
"   2.  ST_INO Inode number.\n"\
"   3.  ST_DEV Device inode resides on.\n"\
"   4.  ST_NLINK  Number of links to the inode.\n"\
"   5.  ST_UID User id of the owner.\n"\
"   6.  ST_GID Group id of the owner.\n"\
"   7.  ST_SIZE Size in bytes of a plain file.\n"\
"   8.  ST_ATIME Time of last access.\n"\
"   9.  ST_MTIME Time of last modification.\n"\
"   10. ST_CTIME Time of last metadata change."
tout_help  = "Usage: tout new_val -- Set / Reset timeout in seconds"
ekey_help  = "Usage: ekey encryption_key -- Set encryption key "
sess_help  = "Usage: sess session data -- Set session key "
xxxx_help  = "Usage: no data"

# ------------------------------------------------------------------------
# Table driven server state machine.
# The table is searched for a mathing start_state, and the corresponding
# function is executed. The new state set to end_state

state_table = [
            # Command ; start_state ; end_state ; action func   ; help func
            ("user",    auth_sess,  auth_user,  get_user_func,  user_help),
            ("pass",    auth_user,  auth_pass,  get_pass_func,  pass_help),
            ("akey",    initial,    auth_key,   get_akey_func,  akey_help),
            ("xkey",    all_in,     none_in,    get_xkey_func,  ekey_help),
            ("ekey",    all_in,     none_in,    get_ekey_func,  ekey_help),
            ("sess",    auth_key,   auth_sess,  get_sess_func,  sess_help),
            ("file",    auth_sess,  got_fname,  get_fname_func, file_help),
            ("fget",    in_idle,    in_idle,    get_fget_func,  fget_help),
            ("data",    got_fname,  in_idle,    get_data_func,  data_help),
            ("uadd",    auth_in,    none_in,    get_uadd_func,  uadd_help),
            ("kadd",    auth_in,    none_in,    get_kadd_func,  kadd_help),
            ("udel",    auth_in,    none_in,    get_udel_func,  udel_help),
            ("ver",     all_in,     none_in,    get_ver_func,   vers_help),
            ("hello",   all_in,     none_in,    get_hello_func, hello_help),
            ("quit",    all_in,     none_in,    get_exit_func,  quit_help),
            ("exit",    all_in,     none_in,    get_exit_func,  quit_help),
            ("help",    all_in,     none_in,    get_help_func,  help_help),
            ("ls",      auth_in,    none_in,    get_ls_func,    lsls_help),
            ("lsd",     auth_in,    none_in,    get_lsd_func,   lsld_help),
            ("cd",      auth_in,    none_in,    get_cd_func,    cdcd_help),
            ("pwd",     auth_in,    none_in,    get_pwd_func,   pwdd_help),
            ("stat",    auth_in,    none_in,    get_stat_func,  stat_help),
            ("tout",    auth_in,    none_in,    get_tout_func,  tout_help),
            ("uini",    all_in,     none_in,    get_uini_func,  uini_help),
            #("kini",    all_in,     none_in,    get_kini_func,  kini_help),
            ]
# ------------------------------------------------------------------------

class StateHandler():

    def __init__(self, resp):
        # Fill in class globals
        self.curr_state = initial
        self.resp = resp
        self.resp.fname = ""
        self.resp.user = ""
        self.resp.cwd = os.getcwd()
        self.resp.dir = ""
        self.resp.ekey = ""
        self.wr = pywrap.wrapper()
        #self.wr.pgdebug = 2

    # --------------------------------------------------------------------
    # This is the function where outside stimulus comes in.
    # All the workings of the state protocol are handled here.
    # Return True from handlers to signal session terminate request

    def run_state(self, strx):
        ret = None

        if self.pgdebug > 5:
            print("Run state data: '" + strx + "'")
        try:
            ret = self._run_state(strx)
        except:
            support.put_exception("While in run state(): " + str(self.curr_state))
            sss =  "ERR on processing request."
            self.resp.datahandler.putdata(sss, self.resp.ekey)
            ret = False
        return ret

    def _run_state(self, strx):
        got = False; ret = True

        if self.pgdebug > 8:
            print( "Incoming strx: ", type(strx), strx)

        dstr = ""
        try:
            dstr = self.wr.unwrap_data(self.resp.ekey, strx)
            #dstr = self.wr.unwrap_data("", strx)
        except:
            sss =  "ERR cannot unwrap / decode data."
            #support.put_exception("While in _run state(): " + str(self.curr_state))
            print("pystate.py %s" % (sss,));
            self.resp.datahandler.putdata(sss, self.resp.ekey)
            return False

        if self.pgdebug > 3:
            print( "Incoming Line: ", dstr)

        comx = dstr[1] #.split()

        if self.pgdebug > 1:
            print( "Com:", "'" + comx[0] + "'", "State =", self.curr_state)

        got = False; comok = False
        # Scan the state table, execute actions, set new states
        for aa in state_table:
            # See if command is in state or all_in is in effect
            # or auth_in and stat > auth is in effect -- use early out
            if comx[0] == aa[0]:
                comok = True
                if self.pgdebug > 3:
                    print("Found command, executing:", aa[0])

                cond = aa[1] == self.curr_state
                if not cond:
                    cond = cond or (aa[1] == auth_in and self.curr_state >= in_idle)
                if not cond:
                    cond = cond or aa[1] == all_in
                if cond:
                        # Execute relevant function
                        ret = aa[3](self, comx)
                        # Only set state if not all_in / auth_in
                        if aa[2] != none_in:
                            self.curr_state = aa[2]
                        got = True
                        break

        # Not found in the state table for the current state, complain
        if not got:
            #print( "Invalid command or out of sequence command ", "'" + comx[0] + "'")
            if not comok:
                sss =  "ERR Invalid command " + "'" + comx[0] + "'"
            else:
                sss =  "ERR Out of Sequence command " + "'" + comx[0] + "'"
            #self.resp.datahandler.putdata(sss.encode("cp437"), self.resp.ekey)
            self.resp.datahandler.putdata(sss, self.resp.ekey)
            # Do not quit, just signal the error
            ret = False
        return ret

# EOF
