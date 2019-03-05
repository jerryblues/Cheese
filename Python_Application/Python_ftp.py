# coding=utf-8

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import socket

# guide: https://my.oschina.net/kangvcar/blog/1599867

port = 2121
localip = socket.gethostbyname(socket.gethostname())
print "Local IP:", localip
print "starting FTP server on:\nftp://5cg7316jvn:%s" % port

authorizer = DummyAuthorizer()
# authorizer.add_user('user', '12345', 'd:\\share', perm='elradfmwMT')
authorizer.add_anonymous('d:\\share')

handler = FTPHandler
handler.authorizer = authorizer

server = FTPServer((localip, port), handler)
server.serve_forever()
