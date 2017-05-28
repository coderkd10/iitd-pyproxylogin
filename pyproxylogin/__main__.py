from .persistent import PersistentLogin

import getpass
import signal

def main():
	# Python 2/3 agnostic safe user input 
	get_input = getattr(__builtins__, 'raw_input', input)

	proxy_code = get_input("The proxy server is : 10.10.78.")
	userid = get_input("Enter your Userid : ")
	try:
		password = getpass.getpass("Enter your password : ")
	except getpass.GetPassWarning:
		print("Free advice: Cover your screen, just in case..")

	print("(Press Ctrl+C to Exit)")
	login = PersistentLogin(proxy_code, userid, password)
	# Quit on Ctrl+C
	def keyboard_interupt_handler(signal, frame):
		print('\nInterrupt received, quitting...')
		login.stop()
	signal.signal(signal.SIGINT, keyboard_interupt_handler)
	login.start() # start login loop

if __name__ == "__main__":
	main()
