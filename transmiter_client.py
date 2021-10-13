"""
[Brief]
transmit files through tcp (sender)

[Usage]
python3 transmiter_client.py file_name   
the filename can be absolute or relative path, file or directory

server_host: xx    (Configure according to the actual IP address of the server)
server_port: 9000  (Consistent with the server side)
"""

import socket, time
import os, json, sys


def list_files(path):
    results = []
    lsdirs = os.listdir(path)
    dirs = []
    for lsdir in lsdirs:
        name = os.path.join(path, lsdir)
        if os.path.isdir(name):
            results += list_files(name)
        else:
            results.append(name)
    return results


class TransmitClient:
    def __init__(self):
        self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_host = "192.168.1.112" # "169.254.106.113"
#        self.server_host = socket.gethostname()
        self.server_port = 9000
        self.socket_client.connect((self.server_host, self.server_port))
        self.send_batch_size = 1024

    def close(self):
        self.socket_client.close()

    def transmit_file(self, target_file, total_cnt=1, seq=1):
        if not os.path.exists(target_file):
            return False
            
        file_size = os.path.getsize(target_file)
        file_info = {"name": target_file, "size": file_size,
                     "total_cnt": total_cnt, "seq": seq}
        print("transmit %d/%d  file: %s  size: %d bytes" %(seq, total_cnt, target_file, file_size))
        self.socket_client.send(json.dumps(file_info, ensure_ascii=False).encode())
        response = self.socket_client.recv(1024)
        
        sent_size = 0
        remaind_size = file_size - sent_size
        with open(target_file, 'rb') as f:
            while True:
                if remaind_size <= 0:
                    break
                elif remaind_size < self.send_batch_size:
                    data = f.read(remaind_size)
                    self.socket_client.send(data)
                    sent_size += remaind_size
                else:
                    data = f.read(self.send_batch_size)
                    self.socket_client.send(data)
                    sent_size += self.send_batch_size
                    
                remaind_size = file_size - sent_size
        
        return True

    def transmit(self, target_file):
        if not os.path.exists(target_file):
            return False
        if not os.path.isdir(target_file):
            return self.transmit_file(target_file)
        files = list_files(target_file)
        total_cnt = len(files)
        for i in range(total_cnt):
            file = files[i]
            self.transmit_file(file, total_cnt=total_cnt, seq=i+1)


def main(argv):
    if len(argv) < 2:
        print("please input a file name!")
        return
    target = argv[1]
    
    # if the input is absolute path, change work directory to its last directory
    # and modify absolute target to relative path
    if os.path.isabs(target):
        
        if os.path.isfile(target):
            work_dir = os.path.join(os.path.dirname(target))
            target = os.path.basename(target)
            os.chdir(work_dir)
        else:  # directory
            work_dir = os.path.join(target, "../")
            os.chdir(work_dir) # chdir before get relpath
            target = os.path.relpath(target)  # the path relate to work_dir
            
            
            
    print(target, os.getcwd())
    app = TransmitClient()
    app.transmit(target)
    app.close()


main(sys.argv)
