#import Library
import os
import pyfiglet
import sys
import socket
import threading
from datetime import datetime

#Clearing Terminal
os.system('cls')

#Title
ascii_banner = pyfiglet.figlet_format("PORT SCANNER V0.4")
print(ascii_banner)

#Ask IPv4 input
remoteServer = input("Enter an IPv4 Adresse : ")
remoteServerIP = socket.gethostbyname(remoteServer)

#Testing RemoteServer Connectivity


#Print a nice banner with information on which host we are about to scan
print ("_" * 60)
print("Scanning Target: " + remoteServerIP)
print("Scanning started at: " + str(datetime.now()))
print ("_" *60)

#Check the date and time the scan was started
t1 = datetime.now()

#Using the range function to specify ports
#Also we will do error handling
try:
	
	# will scan ports between 1 to 65,535
	for port in range(1,65535):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		socket.setdefaulttimeout(.5)
		
		# returns an error indicator
		result = s.connect_ex((remoteServerIP,port))
		if result ==0:
			print("Port {} is open".format(port))
		s.close()
		
except KeyboardInterrupt:
		print("\n Exiting Program !!!!")
		sys.exit()
except socket.gaierror:
		print("\n Hostname Could Not Be Resolved !!!!")
		sys.exit()
except socket.error:
		print("\ Server not responding !!!!")
		sys.exit()

#Checking ending time
t2 = datetime.now()

#Calculate the difference in time to now how long the scan took
total = t2 - t1

#Printing the information on the screen
print ("Scanning Completed in ", total)