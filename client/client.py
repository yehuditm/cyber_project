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

my_socket = None


class Handle():
    def __init__(self):
        self.reset_file_data()

    def reset_file_data(self):
        self.file_name = 'myFile.txt'
        self.file_id = -1
        self.size_of_data = 0
        self.file_index = -1

    def append_to_file(self, fileTransfer):
        if fileTransfer.id is not self.file_id or self.file_index + 1 is not fileTransfer.index:
            return False

        with open(self.file_name, 'ab') as f:
            f.write(fileTransfer.data)

        if fileTransfer.isLast:
            self.reset_file_data()

    def start_get_file(self, fileStart):
        self.file_id = fileStart.id
        self.size_of_data = fileStart.size_of_data
        print "id", self.file_id, "size_of_data", self.size_of_data

    def handle_request(self, data):
        d = data_pb2.TData()
        d.ParseFromString(data)
        if d.WhichOneof("Msg") == "clientReq":
            print '\r[from server] name:', d.clientReq.name
            print 'id:', d.clientReq.id
        if d.WhichOneof("Msg") == "serverRsp":
            if d.serverRsp.WhichOneof("Type") == "fileStart":
                self.start_get_file(d.serverRsp.fileStart)
            if d.serverRsp.WhichOneof("Type") == "fileTransfer":
                self.append_to_file(d.serverRsp.fileTransfer)
                print 'fileTransfer.id', d.serverRsp.fileTransfer.id, 'fileTransfer.size', d.serverRsp.fileTransfer.size
            if d.serverRsp.WhichOneof("Type") == "cmdCommand":
                pass


def main():
    """
    The function sends data to server, and prints msgs from other clients.
    :return:
    """
    try:
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        my_socket.connect((SERVER_ADDRESS, PORT))
        handle = Handle()
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
                    d = data_pb2.TData()
                    if d.WhichOneof("Msg") is None:
                        # d.clientReq.name = msg
                        # d.clientReq.id = 10
                        d.serverRsp.id = 234
                        d.serverRsp.fileStart.id = 234
                        d.serverRsp.fileStart.size_of_data = 321
                        my_socket.send(d.SerializeToString())
                        print "---"
                        d.serverRsp.fileTransfer.id = 234
                        d.serverRsp.fileTransfer.index = 1
                        d.serverRsp.fileTransfer.size = 1
                        d.serverRsp.fileTransfer.isLast = True
                        d.serverRsp.fileTransfer.data.extend([1, 32, 43432])
                        my_socket.send(d.SerializeToString())
                        d.serverRsp.fileTransfer.id = 234
                        d.serverRsp.fileTransfer.index = 2
                        d.serverRsp.fileTransfer.size = 1
                        d.serverRsp.fileTransfer.isLast = True
                        d.serverRsp.fileTransfer.data.extend([1, 32, 43432])
                        my_socket.send(d.SerializeToString())
                        print "---"

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
                handle.handle_request(data)

    except Exception as e:
        print e.message
        my_socket.close()
        print 'connection closed'
        return

    my_socket.close()
    print 'connection closed'


if __name__ == "__main__":
    main()
