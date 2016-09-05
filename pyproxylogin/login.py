#!/usr/bin/env python

# Author      : J Phani Mahesh
# Description : A python utility to log into IITD proxy servers.

from __future__ import print_function

import requests
import sys
from getpass import getpass,GetPassWarning
import time
#import argparse
import configparser
# TODO : If modules don't exist, offer to download them.

from api import get_sessionid, login, refresh, logout
from api import SUCCESSFUL_LOGIN, SUCCESSFUL_LOGOUT

import inspect, os
project_root = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
default_ca_certificate_path = os.path.join(project_root,"CCIITD-CA.crt")

requests.packages.urllib3.disable_warnings() #disable warnings
# TODO : Argument parsing
#Define a special confusing useless(?) wrapper function to accept user input.
def read_input(prompt,retries=3):
    while retries>0:
        try:
            inp=raw_input(prompt)
            if inp!='':
                return inp
            else:
                print("\nI demand input!!!\nHow dare you give an empty reply?")
                retries -= 1
                continue 
        except EOFError:
            print("\nI demand input!!!\nHow dare you throw a EOF at me?")
            retries -= 1
    print("RAGEQUIT!!") # :-(
    sys.exit(255)

# Configuration file parsing and setting variables
config=configparser.ConfigParser()
config.read('pyproxylogin.conf')
try:
    conf=config['PROXY']
except KeyError as e:
    config['PROXY']={}
    conf=config['PROXY']
finally:
    # proxycat=conf['proxycat'] if 'proxycat' in conf else read_input("Enter proxy: http://www.cc.iitd.ernet.in/cgi-bin/proxy.")
    proxyserv=conf['proxyserv'] if 'proxyserv' in conf else read_input("The proxy server is : 10.10.78.")
    address='https://proxy'+proxyserv+'.iitd.ernet.in/cgi-bin/proxy.cgi'
    userid=conf['userid'] if 'userid' in conf else read_input("Enter your Userid : ")
    if 'password' in conf:
        print("WARNING: You have saved your password in PLAINTEXT!")
        passwd=conf['password']
    else:
        try:
            passwd=getpass("Enter your password : ")
        # This tries its best not to echo password
        except GetPassWarning:
            print("Free advice: Cover your screen, just in case..")
    ca_certificate = conf['ca_certificate'] if 'ca_certificate' in conf else default_ca_certificate_path

# Le confirmation messages
# print("Using category",proxycat)
# print("PAC :",auto_proxy)
print("Login address:",address)
print("Reading login page...")


sessionid = get_sessionid(proxyserv)
print("Login page loaded succesfully")

# TODO : Exception handling. Add some intelligence buddy.
print("The session id is : "+sessionid)

def check_login(res):
    if res['status'] == SUCCESSFUL_LOGIN:
        print("You are now logged in.")
    else:
        print("Login Error.\nres = {res}".format(res=res), file=sys.stderr)
        sys.exit(1)

res = login(proxyserv, userid, passwd, sessionid)
check_login(res)

# Le Keep-me-logged-in thingy
try:
    while True:
        time.sleep(240)
        res = refresh(proxyserv, sessionid)
        check_login(res)
except KeyboardInterrupt as e:
    print("Keyboard Interrupt recieved.")
    res = logout(proxyserv, sessionid)
    if res['status'] == SUCCESSFUL_LOGOUT:
        print("Logged out succesfully.")
    else:
        print("Logout Failed.")
    print("""
Thank you for using pyproxylogin.
Report any problems encountered to J Phani Mahesh.
He can be reached at phanimahesh.ee510 [at] ee.iitd.ac.in
Have a nice day!
""")
    sys.exit(0)
  # It is customary to exit with zero status on success
