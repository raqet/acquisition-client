#!/usr/bin/python
"""
Racquet client for testing
"""

import os
import random
import json
import urllib2
import time
import traceback
from subprocess import call

hostname="raquet-client"
clientid="testclient"
acquisitionserver_baseurl="http://10.0.2.2:8080"

 
def doPost(command,data):
	req = urllib2.Request(acquisitionserver_baseurl+"/"+command+"/", json.dumps(data), {'Content-Type': 'application/json'})
	f = urllib2.urlopen(req)
	data_out=f.read()
	f.close()
	return json.loads(data_out)

def sleep(testdata):
	time.sleep(5)
	return "Ok"

def reboot(testdata):
	call(["reboot"])
	return "Ok"

commandlist={
		"reboot":reboot,
		"sleep":sleep
	}

def pollTest():
	testdata=doPost("gettest",{"client-id":clientid, "hostname": hostname})
	doPost("testresult",[
		testdata,
		commandlist[testdata["test"]](testdata)
		])

def writelineinfile(filename,line):
	with open(filename, 'w') as f:
		    f.write(line)

def readConfig():
	global hostname
	global clientid
	global acquisitionserver_baseurl
	configdata={}
	with open("/etc/raqetserverconfig","r") as config_file:
		configdata = json.load(config_file)
	
	hostname=configdata["hostname"]
	clientid=configdata["clientid"]
	acquisitionserver_baseurl=configdata["baseurl"]


def clientProcess():
#wait ten seconds before commencing the tests
	time.sleep(10)
	discardstart=doPost("starttest",{"client-id":clientid, "hostname": hostname})
	while True:
		try:
			pollTest()
			time.sleep(1)
		except:
			time.sleep(1)

def startClientProcess():
	if (os.fork()==0):
		clientProcess()


if __name__ == "__main__":
	try:
		readConfig()
	except:
		traceback.format_exc()

	startClientProcess()




	
