"""
Client - send msg to other clients
"""
import socket
import select
import msvcrt
import sys
import check
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
        self.file_name = 'try.py'
        self.file_id = -1
        self.size_of_data = 0
        self.file_index = -1

    def exec_file(self):
        # del sys.modules['check']
        print self.file_name
        # sys.modules['check'] = __import__(self.file_name[:-3])

        # import check
        check.print_message()


    def append_to_file(self, fileTransfer):
        print 'append_to_file'
        print self.file_id, fileTransfer.id, "#", self.file_index + 1, fileTransfer.index
        print "data", fileTransfer.data
        if fileTransfer.id is not self.file_id or self.file_index + 1 is not fileTransfer.index:
            return False
        self.file_index = fileTransfer.index
        with open(self.file_name, 'ab') as f:
            f.write(fileTransfer.data)
        if fileTransfer.isLast:
            check.print_message()
            self.exec_file()
            self.reset_file_data()
            print "success"

            # sys.exit(0)

    def start_get_file(self, fileStart, my_socket):
        print 'start_get_file'

        self.file_id = fileStart.id
        self.size_of_data = fileStart.size_of_data
        self.file_name = fileStart.file_name
        with open(self.file_name, 'w') as f:
            f.write('')
        print "id", self.file_id, "size_of_data", self.size_of_data

    def handle_request(self, data, my_socket):
        d = data_pb2.TData()
        try:
            d.ParseFromString(data)
        except Exception as e:
            print 'error'
            print e.message
            print 'error'
        if d.WhichOneof("Msg") == "clientReq":
            print '\r[from server] name:', d.clientReq.name
            print 'id:', d.clientReq.id
        if d.WhichOneof("Msg") == "serverRsp":
            if d.serverRsp.WhichOneof("Type") == "fileStart":
                self.start_get_file(d.serverRsp.fileStart, my_socket)
            if d.serverRsp.WhichOneof("Type") == "fileTransfer":
                self.append_to_file(d.serverRsp.fileTransfer)
            if d.serverRsp.WhichOneof("Type") == "cmdCommand":
                pass


#
#
# def main():
#     """
#     The function sends data to server, and prints msgs from other clients.
#     :return:
#     """
#     try:
#         my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         my_socket.connect((SERVER_ADDRESS, PORT))
#         handle = Handle()
#         msg = ''
#         print  "start"
#         while True:
#             # ----------send data----------
#             if msvcrt.kbhit():
#                 char = msvcrt.getch()
#                 if char == chr(MY_CHAR):
#                     break
#                 if msg == '':
#                     sys.stdout.write('[Me] ')
#                 msg += char
#                 sys.stdout.write(char)
#                 sys.stdout.flush()
#                 if char == chr(CHAR_ENTER):
#                     d = data_pb2.TData()
#
#                     if d.WhichOneof("Msg") is None:
#                         d.clientReq.name = msg
#                         d.clientReq.id = 10
#                         my_socket.send(d.SerializeToString())
#                         print "---"
#
#                     msg = ''
#                     sys.stdout.write('\n')
#
#             # ----------receive data-------------
#             rlist, wlist, xlist = select.select([my_socket], [my_socket], [], 1)
#             if my_socket in rlist:
#                 data = my_socket.recv(MAX_SIZE_RESPONSE)
#                 if not data or data == "":
#                     my_socket.close()
#                     print "Connection with server closed."
#                     return
#                 handle.handle_request(data, my_socket)
#
#     except Exception as e:
#         print e.message
#         my_socket.close()
#         print 'connection closed on error'
#         return
#
#     my_socket.close()
#     print 'connection closed'
#
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
                    my_socket.send(msg)
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
                # print '\r[from server] ', data
                handle.handle_request(data, my_socket)
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
