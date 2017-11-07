import socket
import subprocess
import time
import pytest


class TCPClient:
    def __init__(self):
        self.server_address = ('127.0.0.1', 11111)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        retry_times = 0
        while retry_times < 3:
            if 0 == self.sock.connect_ex(self.server_address):
                break
            time.sleep(1)
            retry_times = retry_times + 1
        if retry_times == 3:
            assert False, 'cannot connect server'

    def send(self, msg):
        self.sock.send(msg)

    def recv(self):
        return self.sock.recv(512)

    def close(self):
        self.sock.close()


@pytest.fixture(autouse=True)
def server(request):
    subpro = subprocess.Popen("./server.out")

    def teardown():
        subpro.kill()

    request.addfinalizer(teardown)


@pytest.fixture()
def client(request):
    tcp_client = TCPClient()

    def teardown():
        tcp_client.close()

    request.addfinalizer(teardown)
    return tcp_client


# def test_tcp_server(client):
#     words = ['Hello', 'Hi', 'bye']
#     for word in words:
#         client.send(word)
#         assert word == client.recv()

@pytest.mark.parametrize('aaa', ('Hello', 'Hi', 'bye'))
def test_tcp_server(client, aaa):
    client.send(aaa)
    print '\n', aaa
    assert aaa == client.recv()


if __name__ == '__main__':
    pytest.main("test_sct.py")
