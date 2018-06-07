import socket

import select

SERVER_ADDRESS = "localhost"
PORT = 12345
UNACCEPTED_CONNECTIONS = 5

server_socket = socket.socket()
server_socket.bind((SERVER_ADDRESS, PORT))
server_socket.listen(UNACCEPTED_CONNECTIONS)
open_client_sockets = []

while True:
    rlist, wlist, xlist = select.select([server_socket] + open_client_sockets,
                                        open_client_sockets, [])
    for current_socket in rlist:
        if current_socket is server_socket:
            (new_socket, address) = server_socket.accept()
            open_client_sockets.append(new_socket)
        else:
            print 'New data from client!'
            try:
                data = current_socket.recv(1024)
                if not data or data == "":
                    open_client_sockets.remove(current_socket)
                    print "Connection with client closed."
                else:
                    print data
            except Exception as e:
                open_client_sockets.remove(current_socket)
                print "Connection with client closed."
