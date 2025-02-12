import os
import pyfiglet
import socket
import threading
from queue import Queue
import time
from datetime import datetime

# Clearing Terminal
os.system('cls')

# ASCII Title Banner
ascii_banner = pyfiglet.figlet_format("HORAMA:\nPORT SCANNER V0.1")
print(ascii_banner)


# A print_lock is what is used to prevent "double" modification of shared variables.
# this is used so while one thread is using a variable, others cannot access
# it. Once done, the thread releases the print_lock.
# to use it, you want to specify a print_lock per thing you wish to print_lock.
print_lock = threading.Lock()

# Ask IPv4 input
remoteServer = input("Enter an IPv4 Adresse : ")
target = socket.gethostbyname(remoteServer)


# Print a nice banner with information on which host we are about to scan
print ("_" * 45)
print("Scanned Target: " + target)
print("Scan start at: " + str(datetime.now()))
print ("_" *45)

# Check the date and time the scan was started
t1 = datetime.now()

# Portscan fonction
def portscan(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.setdefaulttimeout(.5)
    
    try:
        # Returns an error indicator
        con = s.connect((target,port))
        with print_lock:
            print("Port {} is open".format(port))
        con.close()
    except:
        pass

# The threader thread pulls an worker from the queue and processes it
def threader():
    while True:
        # Gets an worker from the queue
        worker = q.get()

        # Run the example job with the avail worker in queue (thread)
        portscan(worker)

        # Completed with the job
        q.task_done()        

# Create the queue and threader 
q = Queue()

# How many threads are we going to allow for
for x in range(200):
     t = threading.Thread(target=threader)

     # Classifying as a daemon, so they will die when the main dies
     t.daemon = True

     # Begins, must come after daemon definition
     t.start()


start = time.time()

# Jobs assigned
for worker in range(1,65535):
    q.put(worker)

# Wait until the thread terminates
q.join()

# Checking ending time
t2 = datetime.now()

# Calculate the difference in time to now how long the scan took
total = t2 - t1

# Printing the information on the screen
print ("_" *45)
print ("Scan Completed in ", total)
print ("_" *45 + "\n")

# Exit the program 
wait = input("Press Enter to Exit.")