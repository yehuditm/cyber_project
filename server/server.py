"""
Server - receives data from many clients and sents the msg to all other clients
"""

import socket
import select
import atexit

SERVER_ADDRESS = "localhost"
PORT = 8081
UNACCEPTED_CONNECTIONS = 5
MAX_SIZE_RESPONSE = 1024


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

    print 'start server'
    while True:
        try:
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
        except Exception as e:
            print e.__doc__
            print e.message
            server_socket.close()


if __name__ == "__main__":
    main()
