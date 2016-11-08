#!/usr/bin/python
# vim: tabstop=8 noexpandtab shiftwidth=8 softtabstop=8
"""
Raqet client
"""

import os
import random
import hashlib
import re
import json
import urllib2
import time
import traceback
import subprocess

hostname="raqet-client"
clientid="123456"
acquisitionserver_baseurl="http://10.199.99.2:8080"

devicemapping=[]
global_diskinformation=[]
global_ethernetmac="00:00:00:00:00:00"
global_hwid="00000000000000000000000000000000"

maxlog=1000
logging=[]

class DiskInfo:
	"""A storage class for disk meta information"""
	def __init__(self,DiskDevicePath):
		try:
			self.sddiskinfo=subprocess.check_output(["sdparm","-i",DiskDevicePath])
		except subprocess.CalledProcessError as _:
			self.sddiskinfo="Error"
			pass
		try:
			self.hddiskinfo=subprocess.check_output(["hdparm","-g","-i",DiskDevicePath])
		except subprocess.CalledProcessError as _:
			self.hddiskinfo="Error"
			pass
		try:
			self.smartdiskinfo=subprocess.check_output(["smartctl","-i",DiskDevicePath])
		except subprocess.CalledProcessError as _:
			self.smartdiskinfo="Error"
			pass

	"""Update the hash object with state from the diskinfo. The finalized hash
	should contain various information of hardware information"""
	def addToHWDigest(self,hwdigest):
		hwdigest.update(self.sddiskinfo)
		hwdigest.update(self.hddiskinfo)
#Leave out the smartctl as its output contains a timestamp and is therefor not just
#hardware dependent. It contains mostly the same information anyway

ifconfigmacpattern = re.compile('HWaddr ([0-9a-fA-F][0-9a-fA-F]:[0-9a-fA-F][0-9a-fA-F]:[0-9a-fA-F][0-9a-fA-F]:[0-9a-fA-F][0-9a-fA-F]:[0-9a-fA-F][0-9a-fA-F]:[0-9a-fA-F][0-9a-fA-F])')

class EthernetInfo:
    """Storage class for ethernet MAC information"""
    def __init__(self,EthernetInterfaceName):
		try:
			stdout=subprocess.check_output(["ifconfig",EthernetInterfaceName])
			match = ifconfigmacpattern.search(stdout)
			if match:
				self.macaddress=match.group(1)
				return
		except subprocess.CalledProcessError as _:
			pass
		self.macaddress=""
    def addToHWDigest(self,hwdigest):
        hwdigest.update(self.macaddress)

class RaqetJsonEncoder(json.JSONEncoder):
	def default(self, o):
		if isinstance(o, DiskInfo):
			return o.__dict__
		return json.JSONEncoder.default(self, o)

def printLog(string):
	global maxlog
	global logging
	print(string)
	with open("/tmp/raqetclient.log", "a") as logfile:
		    logfile.write(string)
		    logfile.write("\n")
	if (len(logging)<maxlog):
		logging.append(string)


def doPost(command,data):
	req = urllib2.Request(acquisitionserver_baseurl+"/clientapi/"+command+"/", json.dumps(data,cls=RaqetJsonEncoder), {'Content-Type': 'application/json'})
	f = urllib2.urlopen(req)
	data_out=f.read()
	f.close()
	return data_out

def registerClient():
	global devicemapping
	global logging
	global global_hwid
	doPost("register",{"clientid":clientid, "hostname": hostname, "hardwareid" : global_hwid ,"devicemapping":devicemapping, "logging":logging})
	logging=[]

def sendDiskInformation():
	global global_diskinformation
	doPost("diskinfo",{"clientid":clientid, "hostname": hostname, "hardwareid" : global_hwid ,"diskinformation":global_diskinformation})



def genuid(length=6):
	result=""
# _ signals an unused local variable for pychecker
	for _ in range(0,length):
		result=result+"%02x"%random.randint(0, 255)
	return result

def genguid():
	return genuid(4)+"-"+genuid(2)+"-"+genuid(2)+"-"+genuid(2)+"-"+genuid(6)

def writelineinfile(filename,line):
	with open(filename, 'w') as f:
		    f.write(line)
def gen_blockpath(device):
	return "/sys/kernel/config/target/core/iblock_0/%s"%device

def create_iblock_storage(device):
	bp=gen_blockpath(device)
	os.makedirs(bp)
	writelineinfile(bp+"/udev_path","/dev/%s"%device)
	writelineinfile(bp+"/control","udev_path=/dev/%s"%device)
	writelineinfile(bp+"/enable","1")

	with open(bp+"/info", 'r') as f:
		printLog(f.read())

	guid=genguid()
	writelineinfile(bp+"/wwn/vpd_unit_serial",guid)
	writelineinfile(bp+"/alua/default_tg_pt_gp/alua_write_metadata","1")

def gen_targetpath(name,uid,targetpathnr):
	return "/sys/kernel/config/target/iscsi/iqn.2003-01.org.linux-iscsi.%s:sn.%s/tpgt_%d" % (name,uid,targetpathnr)

def create_target_port_group(name,uid,interface):
	tp=gen_targetpath(name,uid,1)
	os.makedirs(tp + "/np/%s:3260" % (interface))

def create_storage_node(name,uid,lun,device):
	success=True
	tp=gen_targetpath(name,uid,1)
	bp=gen_blockpath(device)
	os.makedirs(tp + "/lun/lun_%d" % lun)
	try:
		os.symlink(bp, tp + "/lun/lun_%d/" % lun + uid)
	except:
		printLog("Failed to create symlink to iblock device "+device)
		success=False
		pass

	writelineinfile(tp+"/enable","1")

#This code disables authentication
	writelineinfile(tp+"/attrib/authentication","0")
	writelineinfile(tp+"/attrib/generate_node_acls","1")

	return success


#device names is an ordered list of names in the /dev/ filesystem.
#lun 0 corresponds to the first lun in the list

def configure_lio_target(get_devicenames):
	guid=genuid()

	mapping=[]

	for device in get_devicenames:
		try:
			create_iblock_storage(device)
		except:
			printLog("Failed to create iblock storage "+device)

	try:
		create_target_port_group(hostname,guid,"0.0.0.0")
	except:
		printLog("Failed to create target port "+hostname)

	lunid=0

	for device in get_devicenames:
		success=False
		try:
			success=create_storage_node(hostname,guid,lunid,device)
		except:
			printLog("Failed to export blockdevice "+device)
#also for failing exports the lun number is increased to keep the list intact
		mapping.append({"device":device,"success":success,"lun":lunid})
		lunid=lunid+1
	return mapping

def get_diskinformation(get_devicenames):
	diskinformation=[]
	for device in get_devicenames:
		diskinformation.append({"device":device,"diskinfo" :
			DiskInfo("/dev/"+device)})
	return diskinformation

def get_devicenames():
	devicenames=[]
	with open("/proc/partitions", 'r') as f:
		for device_line in f:
			device_line_items=device_line.split()
#skip the header line and intermediate empty line
#['major', 'minor', '#blocks', 'name']
			if ((len(device_line_items)<4) or
				(device_line_items[0]=="major")):
				continue
#
# TODO: May need to filter more, currently CD's are not filtered out.
# By selecting based on minor number %16 only the physical disk is exported
# (not the partitions).
#
			if (int(device_line_items[1])%16==0):
				devicenames.append(device_line_items[3])
#				print device_line_items
#	print devicenames
	return devicenames

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

def displayClientInfo():
	global hostname
	global clientid
	global acquisitionserver_baseurl
	global global_ethernetmac
	global global_hwid

	with file("/dev/console","a+") as console:
		console.write("\n\n\n\n")
		console.write("clientid        %s\n" % clientid)
		console.write("hostname        %s\n" % hostname)
		console.write("MAC             %s\n" % global_ethernetmac)
		console.write("hardware id     %s\n" % global_hwid)
		console.write("\n")
		console.write("URL             %s\n" % acquisitionserver_baseurl)
		console.write("\n\n\n\n")
		ipsecinfo=subprocess.check_output(["ipsec","status"])
		console.write(ipsecinfo)
		console.write("\n\n\n\n")

def clientProcess():
	while True:
		try:
			displayClientInfo()
			registerClient()
			sendDiskInformation()
			time.sleep(30)
		except:
			time.sleep(30)

def startClientProcess():
	if (os.fork()==0):
		clientProcess()

def sethwid(diskInformation,ethernetinfo):
	global global_hwid
	hwdigest= hashlib.md5()
	for disk in diskInformation:
		disk['diskinfo'].addToHWDigest(hwdigest)
	ethernetinfo.addToHWDigest(hwdigest)
	global_hwid=hwdigest.hexdigest()



if __name__ == "__main__":
	try:
		readConfig()
	except:
		traceback.format_exc()

	devicenames=get_devicenames()
	global_diskinformation=get_diskinformation(devicenames)
	ethernetinfo = EthernetInfo("eth0")
	global_ethernetmac = ethernetinfo.macaddress

	sethwid(global_diskinformation,ethernetinfo)

	devicemapping=configure_lio_target(devicenames)

	startClientProcess()
