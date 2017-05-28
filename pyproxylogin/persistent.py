"""
Persistantly login into IITD Proxy
"""

# TODO : replace print statements with logging

from .api import login, refresh, logout
from .api import SESSION_EXPIRED
from .api import InvalidServerResponse

import threading
import sys
import time
from requests.exceptions import RequestException

class PersistentLogin:
    def __init__(self, proxy_code, userid, password, retry=True, retry_interval=10):
        self.proxy_code = proxy_code
        self.userid = userid
        self.password = password
        self.retry = retry
        self.retry_interval = retry_interval

        self._finished = threading.Event()

    def start(self):
        continue_looping = True
        while continue_looping and (not self._finished.isSet()):
            try:
                login_response = login(self.proxy_code, self.userid, self.password)
                if not login_response["success"]:
                    # return login_response["response_code"]
                    print("[Error] Login failed : " + login_response["response_code"])
                    return

                sessionid = login_response["sessionid"]            
                print("You are now logged in. [sessionid = {sessionid}]".format(sessionid=sessionid))
                refresh_interval = login_response["refresh_interval"]

                while not self._finished.isSet():
                    refresh_response = refresh(self.proxy_code, sessionid)
                    if not refresh_response["success"]:
                        print("\n[{level}] Refresh failed : {code}".format(
                            level = "Warn" if refresh_response["response_code"] == SESSION_EXPIRED else "Error",
                            code = refresh_response["response_code"]))
                        if refresh_response["response_code"] == SESSION_EXPIRED: 
                            print("Retrying Login...")
                            break
                        else:
                            print("Quitting.")
                            return
                    else:
                        print("Heartbeat sent at {time}. [OK]".format(time=time.asctime()))
                        sys.stdout.write("\033[F")
                        self._finished.wait(refresh_interval)

            except RequestException as e:
                print("[Warn] Request Exception ocurred : " + type(e).__name__)
                if self.retry:
                    print("Retrying in {retry_interval} s...".format(self.retry_interval))
                    self._finished.wait(self.retry_interval)
                else:
                    print("Quitting.")
                    return
            except InvalidServerResponse as e:
                print("[Error] Received Excepted Response from server : {e}. (maybe API has changed)".format(e=str(e)))
                print("Quitting.")
                return

        if self._finished.isSet():
            logout_response = logout(self.proxy_code, sessionid)
            if login_response["success"]:
                print("Logged out successfully.")
            else:
                print("[Error] Logout failed : " + logout_response["response_code"])

    def stop(self):
        self._finished.set()
