#!/usr/bin/python3
import os
import sys
import subprocess
import unittest

def testequal(a,b):
	if (a==b):
		print ("SUCCESS")
	else:
		print ("FAIL")

def getPortal():
	output=subprocess.check_output(["iscsi-ls","iscsi://localhost:3260"])
	print (output)
	target=output[7:-25]
#Test if iSCSI portal is created (last part is uid)
	return target

def getLun(target,lun):
	command=["iscsi-inq",
	"iscsi://localhost:3260/%s/%d" % (target,lun)]
	try:
		output=subprocess.check_output(command,stderr=subprocess.STDOUT)
	except subprocess.CalledProcessError as e:
		output=e.output
#	print (output)
	return output


def getLunCapacity(target,lun):
	command=["iscsi-readcapacity16",
	"iscsi://localhost:3260/%s/%d" % (target,lun)]
	try:
		output=subprocess.check_output(command,stderr=subprocess.STDOUT)
	except subprocess.CalledProcessError as e:
#		print e
		output=e.output
#	print output
	Size=0
	for line in str(output).split("\n"):
#		print line
		if (line[:11]=="Total size:"):
			Size=int(line[11:])
	return Size

class iSCSI_luns(unittest.TestCase):

  def test_portal(self):
	self.assertEqual(target[:-12],"iqn.2003-01.org.linux-iscsi.testingclient-hostname:sn.")

  def test_lun0(self):
	self.assertEqual(getLunCapacity(target,0),51200)

  def test_lun1(self):
	self.assertEqual(getLunCapacity(target,1),0)

  def test_lun2(self):
	self.assertEqual(getLunCapacity(target,2),66560)


if __name__ == '__main__':
	global target
	target=getPortal()
#	getLun(target,0)
#	getLun(target,1)
#	getLun(target,2)
    	unittest.main()
