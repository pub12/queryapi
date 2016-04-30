from firebase import firebase
import argparse
#import asyncio
#import aiohttp
import urllib.request
from time import gmtime, strftime
import time
import sys
import traceback
import asyncio
import aiohttp
import json
from datetime import datetime
import logging

#1. allow option to debug with parameter - perhaps tornado.log
#2. 

# Usage:
#	wiofeed.py	target:wiolink.firebaseio.com site:192.168.0.203 grove:GroveAirqualityA0 token:bb570b0596744a60b992ca3e35a3ccd2
#

class Feed(object):
	def __init__(self, target, deviceSource, username, password, parameter, variables):
		self.target  = target
		self.deviceSource = deviceSource
		self.username = username
		self.password = password
		self.parameter = parameter
		self.variables = variables

	@asyncio.coroutine
	def readDevice(self):
		logging.debug("Reading device url:" + self.deviceSource)
		try:
			# response = yield from aiohttp.request('GET', self.deviceSource)
			response = yield from aiohttp.request('GET', self.deviceSource)
			# logging.debug('got a response %s, status=%s', response, response.status)
			data = yield from response.read()
			logging.debug('read response %s characters', len(data) )
			jsonData = json.loads(data.decode("utf-8"))
			return jsonData

		except Exception as e:
			err = sys.exc_info()[0]
			print( "data Err={}".format(e ) )
			# _, _, tb = sys.exc_info()
			# traceback.print_tb(tb) #\ Fixed format
			# tb_info = traceback.extract_tb(tb)
			# filename, line, func, text = tb_info[-1]

			# print('An error occurred on line {} in statement {}'.format(line, text))
			# exit(1)


	def write(self, value):
		timestamp = strftime("%Y%m%d%H%M%S")
		print("{0} {1} ".format(timestamp, value))

	# @asyncio.coroutine
	def process(self):
		logging.debug("Processing current device" )
		data = yield from self.readDevice()
		if self.variables:
				for var in self.variables:
			 		if var in data:
			 			self.write(var)
		else:
			self.write(data)
			 			# print("{0} = {1}".format(var, jsonData[var]))


class Firebase(Feed):
	def __init__(self, target, deviceSource, username, password, parameter, variables):
		super(Firebase, self).__init__(target, deviceSource, username, password, parameter, variables)
		self.connect()

	def connect(self):
		#target = self.target
		print( self.target)
		self.firebase = firebase.FirebaseApplication(self.target, None)
	
	def write(self, value):
		super(Firebase, self).write(value)

		timestamp = strftime("%Y%m%d%H%M%S")
		result = self.firebase.post(timestamp, value)
		
		#print result

def getArgs():
	parser = argparse.ArgumentParser(description='Create a continuous data feed from a wiolinke grove device to a target site.')
	parser.add_argument('-t', required=False, help='Target site to send data to')
	parser.add_argument('-u', required=False, help='Username for target site')
	parser.add_argument('-p', required=False, help='Password for target site')
	parser.add_argument('-x', required=False, help='Target site parameter value pair')
	parser.add_argument('-v', required=False, help='List of variables to capture', 	nargs='+')
	#parser.add_argument('-', required=True, help='A unique name for the grove sensor')
	parser.add_argument('-f', required=False, help='Get input from file - all other args ignored')
	parser.add_argument('-s', required=False, help='REST API to query')
	parser.add_argument('-l', required=False, help='Indefinitely loop at poll grove device', default=True)
	parser.add_argument('-i', required=False, help='Override(in seconds) default polling interval.  Default = 10s', default=10)
	return parser.parse_args()


class FeedList(object):
	def __init__(self, filename):
		self.df = DataFile(filename)
		self.sourceRefresh()

	def sourceRefresh(self):
		self.df.read()	
		self.timer = Timer(())

		for item in self.df.getSources():
			if item['active'] == 'False': 
				logging.debug('Skipping inactive record:' + item['id'])
				continue

			logging.debug('processing record:' + str(item) )

			if item['action'] == 'Firebase':
				item['obj'] = Firebase( item['target'], item['source'], '', '', '', item['tags'])
			else:  #Assume item.action == 'Print'
				item['obj'] = Feed(  item['target'], item['source'], '', '', '', item['tags'])

			self.timer.setTimer( item['id'], item['freq'], item['obj'].process )


	def processFeeds(self):
		logging.debug('Processing all feed items')
		for item in self.df.getSources():
			if item['active'] == 'False': continue
			self.timer.processTimer( item['id'] ) 
		
			

class DataFile(object):
	def __init__(self, filename):
		self.filename = filename

	def read(self):
		logging.debug('reading file:' + self.filename )
		with open(self.filename) as json_file:
		    self.data = json.load(json_file)
		    return self.data
		    # for item in self.data:

	def getSources(self):
		return self.data

	def count(self):
		return len(self.data)

class Timer(object):
	def __init__(self, timerList):
		self.resetAll()
		for x in timerList:
			logging.debug("Timer index={}".format(x))
			self.setTimer(x)
	
	def resetAll(self):
		self.current = {}
		self.frequency = {}
		self.callback = {}

	def setTimer(self, timerIndex, freq='', callback=''):
		self.current[ timerIndex ] = datetime.now()
		if freq != ''		: self.frequency[ timerIndex ] = int(freq)
		if callback != ''	: self.callback[ timerIndex ] = callback

	def getDuration(self, timerIndex=0):
		timediff = datetime.now()-self.current[ timerIndex ]
		logging.debug("Timer %s duration %s ", timerIndex, timediff.seconds  )
		return int(timediff.seconds)

	def processTimer(self, timerIndex):
		logging.debug('Processing timer: %s', timerIndex)
		if self.getDuration( timerIndex ) > self.frequency[ timerIndex ]:
			self.setTimer( timerIndex )
			logging.debug('About to do a call back to: %s', self.callback[ timerIndex ])
			asyncio.Task( self.callback[ timerIndex ]() )
			
			
# @asyncio.coroutine
def pollDevices(filename):

	cnstDeviceTimer = 'readDevice'
	cnstRefreshTimer = 'refreshSources'
	cnstDeviceReadFreq = 3
	cnstSourceReadFreq = 60
	fl = FeedList(filename)

	timer = Timer( ( cnstDeviceTimer, cnstRefreshTimer))


	while True:
		#Check for new config every minute.  See if require to run a device read every 30 seconds
		# logging.debug("Sleep )
		if(timer.getDuration( cnstDeviceTimer) >= cnstDeviceReadFreq):
			logging.debug("Device Read timer triggered")
			timer.setTimer( cnstDeviceTimer )
			fl.processFeeds()

		if(timer.getDuration( cnstRefreshTimer ) >= cnstSourceReadFreq ):
			timer.setTimer( cnstRefreshTimer )
			fl.sourceRefresh()
			# print("Number of records {}".format( df.count() ) )
		
		sleepTime = cnstDeviceReadFreq-timer.getDuration(cnstDeviceTimer)
		logging.debug("Sleeping for %s seconds", sleepTime)
		yield from asyncio.sleep( sleepTime )


def main():
	args = getArgs()

	if args.f:
		loop = asyncio.get_event_loop()

		asyncio.Task( pollDevices(args.f) )

		loop.run_forever()
		# loop.run_until_complete( pollDevices(args.f) )
		loop.close()
	
	else:
		if "firebase" in args.t:
			f=Firebase(args.t, args.s, args.u, args.p, args.x, args.v)
		else:
			f=Feed(args.t, args.s, args.u, args.p, args.x, args.v)
	 
		loop = asyncio.get_event_loop()
		loop.run_until_complete( f.readDevice() )
		loop.close()

	

if __name__ == '__main__':
	logging.basicConfig(level=logging.DEBUG, format="[%(lineno)s-%(funcName)s] %(message)s")
	main()