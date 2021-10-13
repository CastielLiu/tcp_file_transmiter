
"""
[Brief]
transmit files through tcp (receiver)

[Usage]
python3 transmiter_server.py

prot: 9000
"""


import socket, sys
import json, os
import time

LISTEN_NEW = 1
LISTEN_STOP = 2
LISTEN_TIMEOUT = 3

class TransmitServer:
    def __init__(self):
        self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_server.settimeout(0.5)
        self.host = socket.gethostname()
        self.port = 9000
        
        self.socket_server.bind((self.host, self.port))
        self.socket_server.listen(5)
        print("start listen clients, file will save in %s" % os.getcwd())

    def listen(self):
        try:
            client, addr = self.socket_server.accept()
            # client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, 3000)
            client.settimeout(1.0)
        except KeyboardInterrupt as e:
            return LISTEN_STOP
        except socket.timeout as e:
            return LISTEN_TIMEOUT

        print("socket connect, client addr：%s" % str(addr))
        incomplete_file_info_str = ""
        received_file_cnt = 0
        while True:
            try:
                file_info_str = client.recv(1024).decode('utf-8')
            except ConnectionAbortedError:
                return LISTEN_NEW

            if len(file_info_str) == 0:
                client.close()
                break
            # print(file_info_str)
            # if parse the file_info_str failed, The file information string is not received completely,
            # We need to save the incomplete information and splice it with the next information,
            # Until the resolution is successful
            try:
                if len(incomplete_file_info_str):
                    file_info_str = incomplete_file_info_str+file_info_str
                file_info = json.loads(file_info_str)
            except Exception as e:
                incomplete_file_info_str = file_info_str
                # print("json parse %s faild." % incomplete_file_info_str)
                # print("faild reason. %s" % e)
                continue
            else:  # file_info parse complete
                incomplete_file_info_str = ""

                # Respond to the client and accept the transfer file
                response = "start".encode()  # start
                client.send(response)
            file_name = file_info['name']
            file_size = int(file_info['size'])
            file_dir = os.path.dirname(file_name)
            total_cnt = int(file_info['total_cnt'])
            file_seq = int(file_info['seq'])

            if len(file_dir) != 0 and not os.path.exists(file_dir):
                # print("file_dir", file_dir)
                os.makedirs(file_dir)
            recv_size = 0
            # print("%d/%d start receive：%s, size: %d. " % (file_seq, total_cnt, file_name, file_size))
            ok = True
            recv_empty_time = None
            with open(file_name, 'wb') as f:
                while recv_size < file_size:
                    value = file_size - recv_size

                    # if recv timeout, data len is 0
                    # if client is closed, system raise exception or data len always 0
                    try:
                        if value > 1024:
                            getdata = client.recv(1024)
                        else:
                            getdata = client.recv(value)
                    except ConnectionAbortedError:
                        print("")
                        print("[ERROR] client closed, transmit %s abort!" % file_name)
                        return LISTEN_NEW
                    except socket.timeout:
                        print("")
                        print("[ERROR] transmit %s timeout!" % file_name)
                        client.close()
                        return LISTEN_NEW

                    if len(getdata) == 0:
                        if recv_empty_time is None:
                            recv_empty_time = time.time()
                        elif time.time() - recv_empty_time > 1.0:
                            print("")
                            print("[ERROR] transmit %s timeout!" % file_name)
                            return LISTEN_NEW
                        continue

                    f.write(getdata)
                    recv_size += len(getdata)

                    percentage = 100.0 * recv_size / file_size
                    log_str = "%d/%d %s %.1f%% size: %d bytes" % (file_seq, total_cnt,
                                                                  file_name, percentage, recv_size)
                    if percentage == 100:
                        print(log_str, end="\n")
                    else:
                        print(log_str, end="\r")
            received_file_cnt = received_file_cnt + 1
            if file_seq == total_cnt:
                print("%d files transmit complete. file saved in %s" % (received_file_cnt, os.getcwd()))
                break
        return LISTEN_NEW


def main():
    app = TransmitServer()
    while True:
        res = app.listen()
        if res == LISTEN_STOP:
            break
        elif res == LISTEN_NEW:
            print("start listen new client, file will save in %s" % os.getcwd())

main()
