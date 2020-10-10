# coding=utf-8

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import socket

'''
build ftp server:
pip install pyftpdlib
python -m pyftpdlib
ftp://127.0.0.1:2121

https://my.oschina.net/kangvcar/blog/1599867
'''

port = 2121
localip = socket.gethostbyname(socket.gethostname())
print("\nLocal IP:", localip)
print("Starting FTP Server on:\nftp://%s:%s" % (localip, port))
print("Or:\nftp://5cg7316jvn:%s" % port)
print("account/pwd:\nadmin/123")

authorizer = DummyAuthorizer()
authorizer.add_user('admin', '123', 'C:/Holmes/share', perm='elradfmwMT')
# authorizer.add_anonymous('C:/Holmes/share', perm='elradfmwMT')

handler = FTPHandler
handler.authorizer = authorizer

server = FTPServer((localip, port), handler)
server.serve_forever()
