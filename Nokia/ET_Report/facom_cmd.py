import socket
import binascii
import logging


__all__ = ['OperationOfFacom']


class OperationOfFacom(object):
    function_code_dict = {'query': '02', 'setup': '05'}
    port_num_dict = {
        '1': '0000',
        '2': '0001',
        '3': '0002',
        '4': '0003',
        '5': '0004',
        '6': '0005'
    }
    command_dict = {
        'query': '0001',
        'powerOn': 'FF00',
        'powerOff': '0000'
    }

    def __init__(self, ip, port=4001):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = int(port)

    def query_status(self, port_num):
        send_message = self._generate_send_message(port_num, 'query', 'query')
        return self._send(send_message, 'query')

    def power_on(self, port_num):
        send_message = self._generate_send_message(
            port_num, 'setup', 'powerOn')
        print ('generate power on message')
        print ('send power on message')
        return self._send(send_message, 'setup')

    def power_off(self, port_num):
        send_message = self._generate_send_message(
            port_num, 'setup', 'powerOff')
        print('generate power off message')
        print('send power on message')
        return self._send(send_message, 'setup')

    def _generate_send_message(self, port_num, function_code, command):
        send_message = '01' + \
            self.function_code_dict[
                function_code] + self.port_num_dict[port_num] + self.command_dict[command]
        CRC_string = self._CRC16(send_message)
        send_message = send_message + CRC_string
        return binascii.a2b_hex(send_message)

    def _CRC16(self, send_message):
        dwCRC = 0xFFFF
        for i in range(0, len(send_message), 2):
            ch = send_message[i:i + 2]
            dwtmp = int(ch, 16) & 0x00FF
            dwCRC = dwCRC ^ dwtmp
            for j in range(8):
                if (dwCRC & 0x0001):
                    dwCRC = dwCRC >> 1
                    dwCRC = dwCRC ^ 0xA001
                else:
                    dwCRC = dwCRC >> 1
        CRC1 = hex(dwCRC & 0x00ff).replace('0x', '')
        CRC2 = hex((dwCRC & 0xff00) >> 8).replace('0x', '')
        CRC_string = CRC1.zfill(2) + CRC2.zfill(2)
        return CRC_string

    def _send(self, send_message, function_code):
        self.socket.connect((self.ip, self.port))
        # print('socket connect')
        # print(send_message)
        self.socket.send(send_message)
        # print('socket send')
        response = self.socket.recv(128)
        # print('socket response')
        self.socket.close()
        # print('socket close')
        return self._check_response(send_message, response, function_code)

    def _check_response(self, send_message, response, function_code='setup'):
        response_of_POWER_ON = [b'\x01\x02\x01\x01`H', b'\x01\x02\x02\x01`\xb8', b'\x01\x02\x03\x01a(', b'\x01\x02\x04\x01c\x18'
, b'\x01\x02\x05\x01b\x88', b'\x01\x02\x06\x01bx']
        response_of_POWER_OFF = [b'\x01\x02\x01\x00\xa1\x88', b'\x01\x02\x02\x00\xa1x', b'\x01\x02\x03\x00\xa0\xe8', b'\x01\x02\x04\x00\xa2\xd8'
, b'\x01\x02\x05\x00\xa3H', b'\x01\x02\x06\x00\xa3\xb8']
        if function_code == 'query':
            # print(response)
            # assert response in response_of_query_list
            if response in response_of_POWER_ON:
                # print('state: power on')
                return 'power_on'
            elif response in response_of_POWER_OFF:
                # print('state: power off')
                return 'power_off'
            else:
                return 'unkown'
        elif function_code == 'setup':
            assert response == send_message
