#!/usr/bin/python3
# Load and Save state variables used in program
#
# Author: Mike Pate
# License: Public Domain

import configparser
import datetime 
import time
import socket

# Create a class to hold user defined values
class configVars(object):

    def __init__(self):
        # Set defaults
        self.zipCode = 77379			## Zip code for weather request - integer
        self.daysDisabled = 2			## Days to disable systems prior to and after rain - integer
        self.checkIncrement = 240		## Amount of time in seconds between weather forecast requests - integer
        self.tempLimit = 50				## Loweest temp to allow watering
        self.lastRain = time.time()-(60*60*24*2)	## Hold epoch of last rain - float
		
    def load(self):
        # Attempt to load the vars from a ini file.
        try:
            with open('rain_monitor.cfg', 'r') as config_file:
                # Read the file with configparser
                config = configparser.ConfigParser()
                config.read_file(config_file)
                # Now grab the attributes from the 'DEFAULT' section of the config file
                self.zipCode = config.getint("DEFAULT", "zipCode")
                self.daysDisabled = config.getint("DEFAULT", "daysDisabled")
                self.checkIncrement = config.getint("DEFAULT", "checkIncrement")
                self.tempLimit = config.getint("DEFAULT", "tempLimit")
                self.lastRain = config.getfloat("DEFAULT", "lastRain")
        except FileNotFoundError:
            # Ignore file not found error, defaults will be used instead
            pass

    def save(self):
        # Attempt to save the vars current value to a ini file.
        with open('rain_monitor.cfg', 'w') as config_file:
            config = configparser.ConfigParser()
            config['DEFAULT'] = {'zipCode': self.zipCode,
                                 'daysDisabled': self.daysDisabled,
								 'checkIncrement': self.checkIncrement,
								 'tempLimit': self.tempLimit,
								 'lastRain': self.lastRain}
            config.write(config_file)

			
# Main program which prompts user to change the user defined vars
def DisplayDeviceInfo ():    
	print("Device Info:")
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("gmail.com",80))
	ipaddr = s.getsockname()[0]
	print (datetime.datetime.now().strftime('%A, %B %d, %Y \n%r'))
	print ('IP: %s' % (ipaddr))
	s.close()