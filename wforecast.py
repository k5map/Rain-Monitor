#!/usr/bin/python3

import json
import urllib.request
# from urllib import urlopen
import RPi.GPIO as GPIO
import time
import datetime
import os
# import Adafruit_RGBCharLCD as LCD

## To run this file automatically at startup, change permission of this file to execute
## If using wireless for network adapter, make sure wireless settings are configured correctly in wlan config so wifi device is available on startup
## edit /etc/rc.local file 'sudo pico /etc/rc.local'
## add "python /home/pi/working-python/weather-json.py &" before line "exit 0"

## Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

## Initialize app variables
cfgFileName = "rain-bypass.cfg"
lastRain = time.time()-(60*60*24*2)		## Hold epoch of last rain - float
rainForecasted = False  ## Is rain forecasted within daysDisabled forecast range - Boolean, global
rainToday = False		## Has it rained today - Boolean
minRain = 0.1 			## Minimum rain (inches) required before disable system
currentTemp = 0.0
## variables saved in config file
zipCode = 77379 		## Zip code for weather request - integer
daysDisabled = 2 		## Days to disable systems prior to and after rain - integer
checkIncrement = 180	## Amount of time in seconds between weather forecast requests - integer
tempLimit = 50			## Loweest temp to allow watering 

## Setup Weather Underground
wground_code = "03948070514b8e9c"
forecast_url = "http://api.wunderground.com/api/" + wground_code + "/forecast10day/q/" + str(zipCode) + ".json"
conditions_url = "http://api.wunderground.com/api/" + wground_code + "/conditions/q/" + str(zipCode) + ".json" 
history_url = "http://api.wunderground.com/api/" + wground_code + "/history_20160527/q/" + str(zipCode) + ".json" 
forecastArray = []
# conditionArray = ['rain','thunderstorm']

## Define LCD pins
lcd_rs = 27
lcd_en = 22
lcd_d4 = 25
lcd_d5 = 24
lcd_d6 = 23
lcd_d7 = 18
lcd_red = 4
lcd_green = 17
lcd_blue = 7	## pin 7 is CE1
lcd_columns = 20
lcd_rows = 4
# Initialize LCD
# lcd = LCD.Adafruit_RGBCharLCD(lcd_rs,lcd_en,lcd_d4,lcd_d5,lcd_d6,lcd_d7,lcd_columns,lcd_rows,lcd_red,lcd_green,lcd_blue)

## Define GPIO pins
RED_LED = 19		## This pin controls a flashing red LED that flashes when data error
YELLOW_LED = 5		## This pin enables flashing yellow LED light when watering disabled
GREEN_LED = 22		## This pin enables green LED when watering enabled
RELAY = 0			## This pin controls relay switch. When ON/True, watering is disabled. Default OFF
GPIO.setup(RED_LED,GPIO.OUT)
GPIO.setup(YELLOW_LED,GPIO.OUT)
GPIO.setup(GREEN_LED,GPIO.OUT)
# ==> Need to fix this  GPIO.setup(RELAY,GPIO.OUT)

## main function
def CheckWeather():
	global lastRain
	
	## This function checks current and forecast weather
	while True:  ## Loop foreever
		try:
			## turn off LEDs
			GPIO.output(RED_LED,GPIO.LOW)
			GPIO.output(YELLOW_LED,GPIO.LOW)
			GPIO.output(GREEN_LED,GPIO.LOW)
            
			print ("-" * 75)
			## ----------------------------------------------------------------------
			print ("### START Checking if it has rained TODAY ###")
			
            ## retrieve current weather data
			response = urllib.request.urlopen(conditions_url)
			html = response.read()
			# Parse XML into array
			jsonData = json.loads(html.decode('utf-8'))

			PrecipToday = float(jsonData['current_observation']['precip_today_in'])
			print ("precip_today_in = " + str(PrecipToday))
			currentTemp = float(jsonData['current_observation']['temp_f'])
			print ("temp_f = " + str(currentTemp))
			if (PrecipToday >= minRain):
#				print ("%s\n" % jsonData['current_observation']['observation_epoch'])
				lastRain = float(jsonData['current_observation']['observation_epoch'])
#			else:
#				rain = 0
			print ("lastRain = " + str(lastRain))
			print ("### END Checking if it has rained TODAY ###\n")

			## ----------------------------------------------------------------------
			print ("### START Checking for rain in forecast range ###")

            ## retrieve forecast weather data
			response = urllib.request.urlopen(forecast_url)
			html = response.read()
			# Parse XML into array
			jsonDataForecast = json.loads(html.decode('utf-8'))

			# reset array
			forecastArray = []
			for x in jsonDataForecast['forecast']['simpleforecast']['forecastday']:
				forecastArray.append([x['date']['pretty'],x['date']['epoch'],x['conditions'],x['pop']])
#			print ("break point 1a")

			for x in range(1, daysDisabled+1):
				print (forecastArray[x][0]+"  -  "+ forecastArray[x][1]+" - "+forecastArray[x][2]+" - "+str(forecastArray[x][3]))
				if (forecastArray[x][3] >= 50):
					rainForecasted = True
					break
				else:
					rainForecasted = False
			print ("rainForecasted = " + str(rainForecasted))
			print ("### END Checking if rain in forecast ###\n")

			## ----------------------------------------------------------------------
			## Determine if watering should be enabled or disabled
			print (jsonData['current_observation']['observation_location']['full'] + " - " + jsonData['current_observation']['observation_time'])
			print ("\tTemp = %.1fF, Rain(inches) = %.2f" % (currentTemp,PrecipToday))
			print ("\tTime since last rain: %s" % str(datetime.timedelta(seconds=(time.time()-lastRain))))
			if (PrecipToday >= minRain):
				print ("\tIt has rained today... Disable watering")
				GPIO.output(YELLOW_LED,GPIO.HIGH)
				# open relay
				# GPIO.output(RELAY,GPIO.HIGH)
			elif ((daysDisabled*86400) > (time.time()-lastRain)):
				print ("\tIt has rained recently... Disable watering")
				GPIO.output(YELLOW_LED,GPIO.HIGH)
				# open relay
				# GPIO.output(RELAY,GPIO.HIGH)
			elif (rainForecasted == True):
				print ("\tRain is in the forecast... Disable watering")
				GPIO.output(YELLOW_LED,GPIO.HIGH)
				# open relay
				# GPIO.output(RELAY,GPIO.HIGH)
			elif (currentTemp < tempLimit):
				print ("\tTemp is below limit... Disable watering")
				GPIO.output(YELLOW_LED,GPIO.HIGH)
				# open relay
				# GPIO.output(RELAY,GPIO.HIGH)
			else:
				print ("\tNo rain is expected... Enable watering")
				GPIO.output(GREEN_LED,GPIO.HIGH)
				# close relay
				# GPIO.output(RELAY,GPIO.LOW)
			print ("\tChecking weather again in %.1f minute(s)\n" % (checkIncrement / 60))
			time.sleep(checkIncrement)
			
		except KeyboardInterrupt:		## user has requested the program to stop
			GPIO.cleanup()
			print ("\n\n### Program stopping")
			break
			
		except:		## Weather data unavailable - either connection error, or network error
#			print ("Unexpected error: ")
#			print (sys.exc_info()[0])
			GPIO.output(RED_LED,GPIO.HIGH)
			print ("*** Unexpected error accessing Weather Underground. \nTrying again in %.1f minute(s)\n" % (checkIncrement / 60))
			time.sleep(checkIncrement)

## This funtion gets the path of this file.  When run at startup, we need full path to access config file
def GetProgramDir():
   try:  ## If running from command line __file__ path is defined
      return os.path.dirname(os.path.abspath(__file__)) + "/"
   except:  ## If __file__ is undefined, we are running from idle ide, which doesn't use this var
      return os.getcwd() + "/"
	
## Start program ======================================================================================================
print ("\n" * 5)

## Load values from config file, or create it and get values
try:	## see if config file exists
	configFile = open(GetProgramDir() + cfgFileName,"r")  ## Attempt to open existing cfg file
	print ("Config file found, loading previous values...")
	
	## Convert zip to int to remove unicode formatting, store in zipCode
	zipCode = int(configFile.readline())
	print ("Checking forecast for Zipcode: ", str(zipCode))

    ## Convert second line to int and store in daysDisabled var
	daysDisabled = int(configFile.readline()) 	
	print ("System will be disabled for %s days prior to and after rain" % str(daysDisabled))
	
	## Conver fourth line to int and store in tempLimit var
	tempLimit = int(configFile.readline()) 
	print ("System will be disabled if temp is below %sF" % str(tempLimit))
	
	## Conver third line to int and store in checkIncrement var
	checkIncrement = int(configFile.readline()) 
	print ("System will wait %s seconds between checks" % str(checkIncrement))
	
	configFile.close()
	
except:	## Exception: config file does not exist, create new
    print ("Config file not found, creating new...")

    ## Request zip code for request
    zipCode = int(input("Enter Zip Code: "))

    ## input number of days system will be disabled prior to rain and after rain
    daysDisabled = int(input("Enter number of days to disable system before/after rain (between 1 and 3): "))

    ## input lowest temp before system will suspend watering
    tempLimit = int(input("Enter number if tempature falls below to disable system: "))

    ## request number of checks in 24 hour period
    checkIncrement = int(input("Enter number of minutes between weather checks (greater than 3): "))
    checkIncrement = checkIncrement * 60  ## convert from minutes to seconds
    
    ## Save user input to new config file
    configFile = open(GetProgramDir() + cfgFileName,"w")
	## Write each item to new line
    configFile.write(str(zipCode) + "\n" + str(daysDisabled) + "\n" + str(tempLimit) + "\n"+ str(checkIncrement) + "\n")   
    configFile.close()
	
##  Begin main loop
CheckWeather()
