import stub_webserver
import cherrypy
import json

"""
Stub webserver to emulate the acquisition server
Client -> Server (Register UID=nnnnnn)
"""

cherrypy.server.socket_host = '0.0.0.0'

tests=[]
tests.append({"test":"reboot","validator":"Endvalidator"})


if __name__ == '__main__':
   stub_webserver.tests=tests
   cherrypy.quickstart(stub_webserver.Register(), '/')
