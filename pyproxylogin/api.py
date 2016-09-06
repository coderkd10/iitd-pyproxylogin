import requests
import inspect
import os
from bs4 import BeautifulSoup

project_root = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
default_ca_certificate_path = os.path.join(project_root,"CCIITD-CA.crt") #get default path for IITD-CA-certificate

NO_PROXY = {'http': None, 'https': None} #Avoid proxy when requesting proxy server

#GENERAL ERRORS
SESSION_EXPIRED = -1
UNKNOWN_ERROR = -2

#LOGIN / REFRESH API response codes
SUCCESSFUL_LOGIN = 0
ALREADY_LOGGED_IN = 1
PROXY_SQUISHED = 2
INVALID_CREDENTIALS = 3

#LOGOUT API response codes
SUCCESSFUL_LOGOUT = 0

def get_proxy_server_address(proxy_server_code, ca_cert=default_ca_certificate_path):
	return "https://proxy{code}.iitd.ernet.in/cgi-bin/proxy.cgi".format(code=proxy_server_code)

def get_sessionid(proxy_server_code, ca_cert=default_ca_certificate_path):
	proxy_page_html = requests.get(get_proxy_server_address(proxy_server_code), 
		proxies=NO_PROXY, verify=ca_cert).text
	soup = BeautifulSoup(proxy_page_html, "html.parser")
	return soup.find('input',{'name':'sessionid'})['value']

def parse_login_response(response):
	if "You are logged in successfully" in response:
		return SUCCESSFUL_LOGIN
	elif "Session Expired" in response:
		return SESSION_EXPIRED
	elif "Error" in response:
		if "already logged in" in response:
			return ALREADY_LOGGED_IN
		elif "You are squished" in response:
			return PROXY_SQUISHED
		else:
			return UNKNOWN_ERROR
	elif "Either your userid and/or password does'not match" in response:
		return INVALID_CREDENTIALS
	else:
		return UNKNOWN_ERROR

def login(proxy_server_code, userid, password, sessionid=None, ca_cert=default_ca_certificate_path):
	if sessionid is None:
		sessionid = get_sessionid(proxy_server_code)
	form_data = {'sessionid':sessionid,'action':'Validate','userid':userid,'pass':password}
	response = requests.post(get_proxy_server_address(proxy_server_code),
		data=form_data, proxies=NO_PROXY, verify=ca_cert).text
	status = parse_login_response(response)
	return {'sessionid':sessionid, 'status':status, 'response':response}

def refresh(proxy_server_code, sessionid, ca_cert=default_ca_certificate_path):
	form_data = {'sessionid':sessionid,'action':'Refresh'}
	response = requests.post(get_proxy_server_address(proxy_server_code),
		data=form_data, proxies=NO_PROXY, verify=ca_cert).text
	status = parse_login_response(response)
	return {'sessionid':sessionid, 'status':status, 'response':response}

def parse_logout_response(response):
	if "you have logged out from the IIT Delhi Proxy Service" in response:
		return SUCCESSFUL_LOGOUT
	elif "Session Expired" in response:
		return SESSION_EXPIRED
	else:
		return UNKNOWN_ERROR

def logout(proxy_server_code, sessionid=None, ca_cert=default_ca_certificate_path):
	if sessionid is None:
		sessionid = get_sessionid(proxy_server_code)
	form_data={'sessionid':sessionid,'action':'logout'}
	response = requests.post(get_proxy_server_address(proxy_server_code),
		data=form_data, proxies=NO_PROXY, verify=ca_cert).text
	status = parse_logout_response(response)
	return {'sessionid':sessionid, 'status':status, 'response':response}
