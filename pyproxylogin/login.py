#!/usr/bin/env python

# Author      : J Phani Mahesh
# Description : A python3 utility to log into IITD proxy servers.
# Home        : http://phanimahesh.github.com/iitd-pyproxylogin
# Blog        : http://phanimahesh.wordpress.com
# Bugs        : Report bugs to phanimahesh.ee510 [at] ee.iitd.ac.in

# Import some modules to scare newbies, or may be to get things done.
# bs4 is BeautifulSoup version4, an awesome HTML/XML parser.
from bs4 import BeautifulSoup as soup #,SoupStrainer as limiter
import requests
import sys
from getpass import getpass,GetPassWarning
import time
#import argparse
import configparser
# TODO : If modules don't exist, offer to download them.

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
                i=i-1
                continue 
        except EOFError:
            print("\nI demand input!!!\nHow dare you throw a EOF at me?")
            i=i-1
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
    proxycat=conf['proxycat'] if 'proxycat' in conf else read_input("Enter proxy: http://www.cc.iitd.ernet.in/cgi-bin/proxy.")
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
print("Using category",proxycat)
# print("PAC :",auto_proxy)
print("Login address:",address)
print("Reading login page...")

proxies = {'http':None,'https':None}
# Loading login page
# try:
html = requests.get(address, proxies=proxies, verify=ca_certificate).text
# except Exception as e:
#     print("There was an error retrieving the login page.\nExiting....")
#     # TODO: Check network and report accordingly. C'mon, be intelligent!
#     sys.exit(1)
print("Login page loaded succesfully")
# print html

# I'm Hungry. Make me a soup.
htmlsoup=soup(html,"html.parser")
sessionid=htmlsoup.input['value']
# TODO : Exception handling. Add some intelligence buddy.
print("The session id is : "+sessionid)

# Le Forms
login_form={'sessionid':sessionid,'action':'Validate','userid':userid,'pass':passwd}
loggedin_form={'sessionid':sessionid,'action':'Refresh'}
logout_form={'sessionid':sessionid,'action':'logout'}

# # Le POST-able binary stream maker
# def yunoencode(form):
#     return urllib.parse.urlencode(form).encode('ascii')

# # Le POST-able binary stream data
# login_data=yunoencode(login_form)
# loggedin_data=yunoencode(loggedin_form)
# logout_data=yunoencode(logout_form)

response=requests.post(address, data=login_form, proxies=proxies, verify=ca_certificate).text
print(response)
print("You are now logged in.")
# TODO : Check if *really* logged in

# Le Functions
def refresh():
    response=requests.post(address, data=loggedin_form, proxies=proxies, verify=ca_certificate).text
    print(response)
    print("Heartbeat sent at "+time.asctime())

def logout():
    response=requests.post(address, data=logout_form, proxies=proxies, verify=ca_certificate).text
    print(response)
    # TODO : Verify if *really* logged out
    print("Logged out succesfully.")

# Le Keep-me-logged-in thingy
try:
    while True:
        time.sleep(240)
        refresh()
except KeyboardInterrupt as e:
    print("Keyboard Interrupt recieved.")
    logout()
    print("""
Thank you for using pyproxylogin.
Report any problems encountered to J Phani Mahesh.
He can be reached at phanimahesh.ee510 [at] ee.iitd.ac.in
Have a nice day!
""")
    sys.exit(0)
  # It is customary to exit with zero status on success
