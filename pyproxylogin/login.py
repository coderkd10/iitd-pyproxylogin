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
    ca_cert = conf['ca_certificate'] if 'ca_certificate' in conf else default_ca_certificate_path

# Le confirmation messages
# print("Using category",proxycat)
# print("PAC :",auto_proxy)
print("Login address:",address)
print("Reading login page...")


sessionid = get_sessionid(proxyserv, ca_cert=ca_cert)
print("Login page loaded succesfully")

# TODO : Exception handling. Add some intelligence buddy.
print("The session id is : "+sessionid)

def check_login(res):
    if res['status'] == SUCCESSFUL_LOGIN:
        return True
    else:
        print("Login Error.\nres = {res}".format(res=res), file=sys.stderr)
        sys.exit(1)

res = login(proxyserv, userid, passwd, sessionid, ca_cert=ca_cert)
if check_login(res):
    print("You are now logged in.")


import threading
class PersistentLogin(threading.Thread):
    def __init__(self, interval=120):
        threading.Thread.__init__(self)
        self._finished = threading.Event()
        self._interval = interval
    def isRunning(self):
        return not self._finished.isSet()
    def terminate(self):
        self._finished.set()
    def run(self):
        while True:
            if self._finished.isSet():
                return
            else:
                self.task()
                self._finished.wait(self._interval)
    def task(self):
        res = refresh(proxyserv, sessionid, ca_cert=ca_cert)
        if check_login(res):
            print("Heartbeat sent at {time}. [OK]".format(time=time.asctime()))
            sys.stdout.write("\033[F")
        else:
            print("Refreshing failed. Exiting...")
            self.terminate()


# # Le Keep-me-logged-in thingy
# from threading import Timer
# def keep_logged_in(interval=5):
#     res = refresh(proxyserv, sessionid, ca_cert=ca_cert)
#     if check_login(res):
#         print("Heartbeat sent at "+time.asctime())
#     t = Timer(interval,keep_logged_in,(interval,))
#     # t.daemon = True
#     t.start()

# import atexit

def logout_on_exit():
    res = logout(proxyserv, sessionid, ca_cert=ca_cert)
    print ("Logging out... Response : \n"+ str(res) +"\n\n")
    if res['status'] == SUCCESSFUL_LOGOUT:
        print("Logged out succesfully.")
    else:
        print("Logout Failed.")


if __name__ == '__main__':

    pl = PersistentLogin(120)
    pl.start()
    
    def gracefully_exit():
        pl.terminate()
        logout_on_exit()
        sys.exit(0)

    def signal_handler(signal, frame):
        print("\nKeyboardInterrupt Handler called...")
        gracefully_exit()

    #import signal
    # signal.signal(signal.SIGINT, signal_handler)
    # ^ Replaced with try & Catch

    while pl.isRunning():
        try:
            ins = raw_input()
            if ins == "EXIT":
                print("Exit Command Received. Exiting...")
                gracefully_exit()
        except (KeyboardInterrupt, EOFError):
            print("\nInterrupt received. Exiting...")
            gracefully_exit()



    # try:
    #     keep_logged_in(120)
    # except KeyboardInterrupt:
    #     print("caught interrupt")
    #     logout_on_exit()
    # print("done!")
