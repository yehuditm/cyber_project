"""
Client - send msg to other clients
"""

import socket
import select
import msvcrt
import sys

import data_pb2

SERVER_ADDRESS = "localhost"
PORT = 8081
MAX_SIZE_RESPONSE = 1024
MY_CHAR = 27
CHAR_ENTER = 13


def main():
    """
    The function sends data to server, and prints msgs from other clients.
    :return:
    """
    try:
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        my_socket.connect((SERVER_ADDRESS, PORT))
        msg = ''
        while True:
            # ----------send data----------
            if msvcrt.kbhit():
                char = msvcrt.getch()
                if char == chr(MY_CHAR):
                    break
                if msg == '':
                    sys.stdout.write('[Me] ')
                msg += char
                sys.stdout.write(char)
                sys.stdout.flush()
                if char == chr(CHAR_ENTER):
                    m_data = data_pb2.TClientReq()
                    m_data.name = msg
                    m_data.id = 10
                    my_socket.send(m_data.SerializeToString())
                    msg = ''
                    sys.stdout.write('\n')

            # ----------receive data-------------
            rlist, wlist, xlist = select.select([my_socket], [my_socket], [], 1)
            if my_socket in rlist:
                data = my_socket.recv(MAX_SIZE_RESPONSE)
                if not data or data == "":
                    my_socket.close()
                    print "Connection with server closed."
                    return
                m_data = data_pb2.TClientReq()
                m_data.ParseFromString(data)
                print '\r[from server] name:', m_data.name
                print '\n'
                print  'id:',m_data.id
                if msg != '':
                    sys.stdout.write('[Me] ' + msg)
                    sys.stdout.flush()

    except Exception as e:
        print e.message
        my_socket.close()
        print 'connection closed'
        return

    my_socket.close()
    print 'connection closed'


if __name__ == "__main__":
    main()
