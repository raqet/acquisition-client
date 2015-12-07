import cherrypy
import json

"""
Stub webserver to emulate the acquisition server
Client -> Server (Register UID=nnnnnn)
"""

cherrypy.server.socket_host = '0.0.0.0'

testnr=0
tests=[]
tests.append({"test":"sleep", "validator":"Okvalidator"})
tests.append({"test":"sleep","validator":"Endvalidator"})

def nullvalidator(data):
	return True

def Okvalidator(data):
	return data[1]=="Ok"

def Endvalidator(data):
	exit()

validators={
		"nullvalidator" : nullvalidator,
		"Okvalidator"  :  Okvalidator,
		"Endvalidator"  :  Endvalidator
	   };

class Register(object):

#Test framework stubs

    @cherrypy.expose("starttest")
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def starttest(self):
	    print "In starttest"
	    global testnr
	    testnr=0
	    return "Ok"

    @cherrypy.expose("gettest")
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def gettest(self):
	    global testnr
	    gettest=cherrypy.request.json
	    print "In gettest"
	    print gettest
	    test=tests[testnr]

	    testnr=testnr+1
	    if(testnr>=len(tests)):
		    testnr=0

	    print test

	    return test

    @cherrypy.expose("testresult")
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def testresult(self):
	    testresult=cherrypy.request.json
	    print "In testresult"
	    print testresult
	    if (True==validators[testresult[0]["validator"]](testresult)):
		    print "SUCCESS"
	    else:
		    print "FAIL"
	    return ""

#Acquisition server stubs
    @cherrypy.expose("register")
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index(self):
	    data=cherrypy.request.json
	    print "In register"
	    print data
	    return "Register"

if __name__ == '__main__':
   cherrypy.quickstart(Register(), '/')
