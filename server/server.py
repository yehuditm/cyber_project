"""
Server - receives data from many clients and sents the msg to all other clients
"""

import socket
import select
import msvcrt
import sys

SERVER_ADDRESS = "localhost"
PORT = 8081
UNACCEPTED_CONNECTIONS = 5
MAX_SIZE_RESPONSE = 1024
MY_CHAR = 27
CHAR_ENTER = 13


def send_waiting_messages(wlist, messages_to_send):
    """
    The function gets list of connections and messages and sent them.
    :param wlist: a list of connections
    :param messages_to_send: a list of messages to send
    :return: a list of messages that not sends yet
    """
    for message in messages_to_send:
        (client_socket, data) = message
        if client_socket in wlist:
            client_socket.send(data)
            messages_to_send.remove(message)
    return messages_to_send


def update_version():
    print 'update'
    pass


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
                            print data
                            for soc in open_client_sockets:
                                if soc != current_socket:
                                    messages_to_send.append((soc, data))

                    except Exception as e:
                        open_client_sockets.remove(current_socket)
                        print "Connection with client closed."

            messages_to_send = send_waiting_messages(wlist, messages_to_send)

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
                        update_version()


        except Exception as e:
            print e.__doc__
            print e.message
            server_socket.close()


if __name__ == "__main__":
    main()
