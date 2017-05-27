import requests
from bs4 import BeautifulSoup
import re

'''
API response codes
'''
# Success codes
SUCCESSFUL_LOGIN    = "SUCCESSFUL_LOGIN"
SUCCESSFUL_LOGOUT   = "SUCCESSFUL_LOGOUT"
# Error codes
SESSION_EXPIRED     = "SESSION_EXPIRED"
INVALID_CREDENTIALS = "INVALID_CREDENTIALS" # userid / password incorrect
SQUISHED            = "SQUISHED"  # proxy quota exceeded
ALREADY_LOGGED_IN   = "ALREADY_LOGGED_IN" # someone already logged in from same IP

# Internal variables
_NO_PROXY = {'http': None, 'https': None} # Avoid proxy when requesting proxy server
PROXY_ADDRESS_FORMAT = "https://proxy{proxy_code}.iitd.ernet.in/cgi-bin/proxy.cgi" # Proxy login server adress format


class InvalidServerResponse(Exception):
    '''
    Exception raised when the server responds in a way other than expected.
    Contains debug_info which contains useful debugging information
    '''
    def __init__(self, *args, **kwargs):
        debug_info = kwargs.pop("debug_info", {})
        self.debug_info = debug_info
        # Call base Exception constructor
        super(InvalidServerResponse, self).__init__(*args, **kwargs)

def proxy_server_address(proxy_code):
    '''
    Get proxy login server address.
    E.g. https://proxy22.iitd.ac.in/cgi-bin/proxy.cgi
    '''
    return PROXY_ADDRESS_FORMAT.format(
        proxy_code=proxy_code)

def _build_requests_options(kwargs):
    '''
    Internal function to generate options to be passed to requests
    '''
    requests_options = {} # options to pass to requests
    requests_options["proxies"] = _NO_PROXY
    if "cert" in kwargs:
        requests_options["verify"] = kwargs["cert"]
    return requests_options

def _raise_unexpected_status_code_ex(proxy_code, requests_options, response):
    '''
    Internal function to raise exception when server responds with an unexpected status code
    '''
    url = proxy_server_address(proxy_code)
    status_code = response.status_code
    raise InvalidServerResponse(
            "Received a status code {status_code} from {url}".
                format(status_code=status_code, url=url),
            debug_info = {
                "proxy_code": proxy_code,
                "url": url,
                "requests_options": requests_options,
                "status_code": response.status_code,
                "response": response
            })

def get_sessionid(proxy_code, **kwargs):
    '''
    Get session id for logging into proxy server
    '''
    url = proxy_server_address(proxy_code)
    requests_options = _build_requests_options(kwargs)
    response = requests.get(
                url,
                **requests_options)
    # check if we get a 200 response code
    if response.status_code != 200:
        _raise_unexpected_status_code_ex(proxy_code, requests_options, response)
    response_html = response.text
    try:
        soup = BeautifulSoup(response_html, "html.parser")
        return soup.find('input',{'name':'sessionid'})['value']
    except Exception as e:
        raise InvalidServerResponse(
                "Cannot find sessionid in server response",
                debug_info = {
                    "proxy_code": proxy_code,
                    "response_html": response_html
                })

def get_refresh_interval(login_response_text):
    '''
    Get the time-interval between refresh API calls, i.e., the heartbeat period.
    Input parameter : Login API response text
    Return : Refresh time interval (in milli-seconds) [int]
    '''
    # Want to find the line : setTimeout('MySubmit1()', 120000);
    interval_regex = re.compile("setTimeout\(.*,\s*(\d*)\)")
    match = interval_regex.search(login_response_text)
    if (match is None) or (len(match.groups()) != 1):
        raise InvalidServerResponse(
            "Cannot find refresh interval in login response",
            debug_info = {
                "login_response_text": login_response_text,
                "match": match
            })
    else:
        try:
            interval = int(match.groups()[0])
            return interval
        except:
            raise InvalidServerResponse(
                "Cannot find refresh interval in login response",
                debug_info = {
                    "login_response_text": login_response_text,
                    "match": match,
                    "interval_string": match.groups()[0]
                })

def parse_login_response(response_text):
    '''
    Parse response text from login/refresh API
    Returns (success, code)
    '''
    if "You are logged in successfully" in response_text:
        return (True, SUCCESSFUL_LOGIN)
    elif "Session Expired" in response_text:
        return (False, SESSION_EXPIRED)
    elif "Error" in response_text:
        if "already logged in" in response_text:
            return (False, ALREADY_LOGGED_IN)
        elif "You are squished" in response_text:
            return (False, SQUISHED)
        else:
            raise InvalidServerResponse("Unknown response from login API",
                    debug_info={"response_text": response_text})
    elif "Either your userid and/or password does'not match" in response_text:
        return (False, INVALID_CREDENTIALS)
    else:
        raise InvalidServerResponse("Unknown response from login API",
                debug_info={"response_text": response_text})

def parse_logout_response(response_text):
    '''
    Parse response from logout API
    Returns (success, code)
    '''
    if "you have logged out from the IIT Delhi Proxy Service" in response_text:
        return (True, SUCCESSFUL_LOGOUT)
    elif "Session Expired" in response_text:
        return (False, SESSION_EXPIRED)
    else:
        raise InvalidServerResponse("Unknown response from login API",
                debug_info={"response_text": response_text})

def login(proxy_code, userid, password, **kwargs):
    '''
    Perform Login
    '''
    # Get session if presesent in kwargs, otherwise get one from server
    if "sessionid" in kwargs:
        sessionid = kwargs.pop("sessionid") # remove session id key if present
    else:
        sessionid = get_sessionid(proxy_code, **kwargs)
    requests_options = _build_requests_options(kwargs)
    form_data = {
                    'sessionid': sessionid,
                    'action': 'Validate',
                    'userid': userid,
                    'pass': password
                }
    url = proxy_server_address(proxy_code)
    response = requests.post(
                url,
                data=form_data,
                **requests_options)
    if response.status_code != 200:
        _raise_unexpected_status_code_ex(proxy_code, requests_options, response)
    success, code = parse_login_response(response.text)
    return_dict = {
        'success': success,
        'response_code': code,
        'sessionid': sessionid,
        'response': response
    }
    if success:
        # Get refresh API period
        refresh_interval = get_refresh_interval(response.text)
        return_dict["refresh_interval"] = refresh_interval
    return return_dict

def refresh(proxy_code, sessionid, **kwargs):
    '''
    Refresh login, i.e, send "heartbeat"
    '''
    requests_options = _build_requests_options(kwargs)
    form_data = {
                    'sessionid':sessionid,
                    'action':'Refresh'
                }
    url = proxy_server_address(proxy_code)
    response = requests.post(
                url,
                data=form_data,
                **requests_options)
    if response.status_code != 200:
        _raise_unexpected_status_code_ex(proxy_code, requests_options, response)
    success, code = parse_login_response(response.text)
    return {
        'success': success,
        'response_code': code,
        'response':response
    }

def logout(proxy_code, sessionid, **kwargs):
    requests_options = _build_requests_options(kwargs)
    form_data = {
                    'sessionid': sessionid,
                    'action':'logout'
                }
    url = proxy_server_address(proxy_code)
    response = requests.post(
                url,
                data=form_data,
                **requests_options)
    if response.status_code != 200:
        _raise_unexpected_status_code_ex(proxy_code, requests_options, response)
    success, code = parse_logout_response(response.text)
    return {
        'success': success,
        'requests_code': code,
        'response': response
    }
