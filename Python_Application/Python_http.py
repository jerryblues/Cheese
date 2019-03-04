# coding=utf-8
'''
D:\code\Cheese\Python_Application\Python_http.py
h4zhang
'''

import SimpleHTTPServer
import SocketServer
import socket
import webbrowser

# simple way to make http server, run at any path:
# python -m SimpleHTTPServer 18080
# http://10.140.179.44:18080

port = 18081
Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
httpd = SocketServer.TCPServer(("", port), Handler)

localip = socket.gethostbyname(socket.gethostname())
path = localip + ':' + str(port)

chromePath = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chromePath))
webbrowser.get('chrome').open(path, new=2, autoraise=True)

print "starting HTTP server on: %s" % path

httpd.serve_forever()
