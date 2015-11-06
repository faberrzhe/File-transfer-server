#!/usr/bin/env python3
import socket, threading, sys, os, select, hashlib
class file_receive(threading.Thread):
    def __init__(self,conn):
        threading.Thread.__init__(self)
        self.conn=conn
    def run(self):
        global work_directory
        while True:
            try:
                data=str(self.conn.recv(1),'utf-8')
            except socket.error:
                    break
            while data[-2:]!='\r\n':
                try:
                    data+=str(self.conn.recv(1),'utf-8')
                except socket.error:
                    break
            filename = data[:-2]
            try:
                data=str(self.conn.recv(1),'utf-8')
            except socket.error:
                    break
            while data[-2:]!='\r\n':
                try:
                    data+=str(self.conn.recv(1),'utf-8')
                except socket.error:
                    break
            filesize = int(data[:-2])
            file = open(work_directory+filename, 'wb')
            while filesize>0:
                if filesize>4096:
                    try:
                        data = self.conn.recv(4096)
                    except socket.error:
                        break
                    datasize=len(data)
                    filesize=filesize-datasize
                    file.write(data)
                else:
                    try:
                        data = self.conn.recv(filesize)
                    except socket.error:
                        break
                    datasize=len(data)
                    filesize=filesize-datasize
                    file.write(data)
            file.close()
            return self.conn,filename

def Parse_index(indexfilename):
    global work_directory,fragmentsize,total_fragments
    with open(work_directory+indexfilename,'rb') as indexfile:
        need_fragments=[]
        filename=work_directory+str(indexfile.readline()[:-2],'utf-8')
        fragmentsize=int(indexfile.readline()[:-2])
        line=str(indexfile.readline()[:-2],'utf-8')
        while line:
            fragmentnumber,index_hashsumd=line.split(" ")
            try:
                file=open(filename+'_part'+fragmentnumber,'rb')
            except FileNotFoundError:
                need_fragments.append(fragmentnumber)
            else:
                fileread=file.read(fragmentsize)
                file_hashsumd=hashlib.md5(fileread).hexdigest()
                if index_hashsumd==file_hashsumd:
                    file.close()
                else:
                    file.close()
                    os.remove(filename+'_part'+fragmentnumber)
                    need_fragments.append(fragmentnumber)
            line=str(indexfile.readline()[:-2],'utf-8')
    total_fragments=int(fragmentnumber)+1
    need_fragments=','.join(need_fragments)
    return need_fragments

class server():
    def __init__(self):
        self.run()
    def solving_file(self,filename):
        global work_directory,total_fragments
        full_file=open(work_directory+filename,'w+b')
        for i in range (total_fragments):
            try:
                fragment_file=open(work_directory+filename+'_part'+str(i),'rb')
            except:
                break
            else:
                data=fragment_file.read()
                full_file.write(data)
                fragment_file.close()
                os.remove(work_directory+filename+'_part'+str(i))
        full_file.close()
        print('Received file '+filename +' To directory: '+work_directory)
        os.remove(work_directory+filename+'.index')
    def run(self):
        global work_directory
        username=os.getlogin()
        if os.name=='nt':
            work_directory='C:/python_receive/'
        else:
            work_directory=os.path.join(os.path.expanduser('~'), 'python_receive/')
        if not os.path.exists(work_directory):
                    try:
                        os.makedirs(work_directory)
                    except:
                        print('Could not create work directory' +work_directory)
                        sys.exit(1)
        sock=socket.socket()
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)
        sock.bind(('',5666))
        sock.listen(50)
        inputs=[sock]
        while inputs:
            r,w,e=select.select(inputs,[],[])
            for current_socket in r:
                conn,addr=current_socket.accept()
                try:
                    flag=str(conn.recv(1),'utf-8')
                except socket.error:
                    break
                while flag[-2:]!='::' and len(flag)<50:
                    try:
                        flag+=str(conn.recv(1),'utf-8')
                    except socket.error:
                        break
                if flag == 'INDEX::':
                    th=file_receive(conn)
                    returned_connection,indexfilename=th.run()
                    print('Receiving indexfile: '+indexfilename)
                    need_fragments=Parse_index(indexfilename)
                    if need_fragments=='':
                        try:
                            returned_connection.send(bytes('DONE::','utf-8'))
                        except socket.error:
                            break
                        self.solving_file(indexfilename[:-6])
                    else:
                        try:
                            returned_connection.send(bytes('GET_FRAGMENTS::' + need_fragments+'::','utf-8'))
                        except socket.error:
                            break

                elif flag== 'FRAGMENT::':
                    th=file_receive(conn)
                    returned_connection,fragment_filename=th.run()
                    try:
                        returned_connection.send(bytes('ACK::','utf-8'))
                    except socket.error:
                        break
                    returned_connection.close()
                else:
                    print('Error')
                    conn.close()


if __name__=="__main__":
    server()
