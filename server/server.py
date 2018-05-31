"""
Server - receives data from many clients and sents the msg to all other clients
"""

import socket
import select
import msvcrt
import sys
import os
import time
import data_pb2
import random

SERVER_ADDRESS = "localhost"
PORT = 8081
UNACCEPTED_CONNECTIONS = 5
MAX_SIZE_RESPONSE = 10240
PIECE_LEN = 1000
MY_CHAR = 27
CHAR_ENTER = 13
MAX_RANDOM = 1000

messages_to_send = []


def read_in_chunks(file_object, chunk_size=PIECE_LEN):
    """Lazy function (generator) to read a file piece by piece.
    Default chunk size: 1k."""
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data


def send_data_to_all(data, current_socket, open_client_sockets, wlist):
    for soc in open_client_sockets:
        if soc != current_socket:
            messages_to_send.append((soc, data))
    send_waiting_messages(wlist)


def send_updates_file(f_name, open_client_sockets, wlist):
    size_of_file = os.path.getsize(f_name)
    file_id = random.randint(1, MAX_RANDOM)
    d = data_pb2.TData()
    print "1"
    d.serverReq.id = file_id
    print "2"
    d.serverReq.fileStart.id = file_id
    print "1"
    d.serverReq.fileStart.size_of_data = size_of_file
    d.serverReq.fileStart.file_name = raw_input("file name: ")
    send_data_to_all(d.SerializeToString(), None, open_client_sockets, wlist)
    print 'd:', d
    time.sleep(1)
    i = 0
    bytes_readed = 0
    with open(f_name, 'rb') as f:
        for piece in read_in_chunks(f):
            bytes_readed += len(piece)
            d.serverReq.fileTransfer.id = file_id
            d.serverReq.fileTransfer.index = i
            d.serverReq.fileTransfer.isLast = (bytes_readed >= size_of_file)
            d.serverReq.fileTransfer.data = piece
            print 'd:', d
            send_data_to_all(d.SerializeToString(), None, open_client_sockets, wlist)
            time.sleep(1)
            i += 1


def send_waiting_messages(wlist):
    """
    The function gets list of connections and messages and sent them.
    :param wlist: a list of connections
    :return: a list of messages that not sends yet
    """
    for message in messages_to_send:
        (client_socket, data) = message
        if client_socket in wlist:
            client_socket.send(data)
            messages_to_send.remove(message)


def handle_request(data, open_client_sockets=[], current_socket=None):
    try:
        d = data_pb2.TData()
        d.ParseFromString(data)
        if d.WhichOneof("Msg") == "clientReq":
            if d.clientReq.WhichOneof("Type") == 'clientStart':
                print d.clientReq.clientStart.ip
                for soc in open_client_sockets:
                    print soc.getpeername()
        if d.WhichOneof("Msg") == 'clientRsp':
            print d.clientRsp.status
            if d.clientRsp.WhichOneof("Type") == 'cmdCommandResult':
                print d.clientRsp.cmdCommandResult.result

                # else:
                #     for soc in open_client_sockets:
                #         if soc != current_socket:
                #             messages_to_send.append((soc, data))
    except Exception as e:
        print e.message


def send_command(cmd, open_client_sockets=None, wlist=None):
    d = data_pb2.TData()
    d.serverReq.cmdCommand.cmd = cmd
    d.serverReq.id = random.randint(1, MAX_RANDOM)
    send_data_to_all(d.SerializeToString(), None, open_client_sockets, wlist)


def main():
    """
    The function opens socket of the server and listen to data that it receives.
    :return:
    """
    server_socket = socket.socket()
    server_socket.bind((SERVER_ADDRESS, PORT))
    server_socket.listen(UNACCEPTED_CONNECTIONS)

    messages_to_send = []
    open_client_sockets = []
    msg = ''
    print 'start server'
    while True:
        try:

            # ----------recieve data----------
            rlist, wlist, xlist = select.select([server_socket] + open_client_sockets,
                                                open_client_sockets, [])
            for current_socket in rlist:
                if current_socket is server_socket:
                    (new_socket, address) = server_socket.accept()
                    open_client_sockets.append(new_socket)
                else:
                    print 'New data from client!'
                    try:
                        data = current_socket.recv(MAX_SIZE_RESPONSE)
                        if not data or data == "":
                            open_client_sockets.remove(current_socket)
                            print "Connection with client closed."
                        else:
                            handle_request(data, open_client_sockets, current_socket)
                    except Exception as e:
                        open_client_sockets.remove(current_socket)
                        print "Connection with client closed."

            send_waiting_messages(wlist)

            # ----------send data----------
            if msvcrt.kbhit():
                char = msvcrt.getch()
                if char == chr(MY_CHAR):
                    break
                msg += char
                sys.stdout.write(char)
                sys.stdout.flush()
                if char == chr(CHAR_ENTER):
                    if msg.startswith('1'):
                        send_updates_file('client.py', open_client_sockets, wlist)
                    elif msg.startswith('2'):
                        send_command("netstat -a -n -o", open_client_sockets, wlist)
                    elif msg.startswith('3'):
                        send_command("ls -l", open_client_sockets, wlist)
                    msg = ''
            send_waiting_messages(wlist)

        except Exception as e:
            print e.__doc__
            print e.message
            server_socket.close()


if __name__ == "__main__":
    main()
