import sys
import socket
import logging
import os
import time
from threading import Thread
import hashlib
import sys
import pathlib
import io

filename=time.strftime("%Y-%m-%d-%H-%M-%S",time.localtime())+"-log.txt"
path=pathlib.Path("server/Logs/"+filename)
pathlib.Path.touch(path)
logging.basicConfig(filename=path,level=logging.DEBUG,
                    format="%(name)s: %(message)s",
                    )

def log(str):
    print(str)
    logging.info(str)

# Python server.py filename clientsnumber
testfile = pathlib.Path("server/"+sys.argv[1])
testclients = sys.argv[2]
concurrentConnections=0
clients=[]



server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ("", 3000)

try:
    server.bind(server_address)
except:
    logging.error(server.error)

server.listen(30)

log("Server Listening on: "+str(server_address))
log("File to send: "+testfile.name+"number of clients: "+testclients)

def calculatemd5(file):
    content = file.read()
    md5=hashlib.md5(content)
    md5str=md5.hexdigest()
    log("Server: File MD5 is "+md5str)
    return md5str

def getData(sock):
    datos = bytearray()
    while True:
        parte = sock.recv(4096)
        datos += bytearray(parte)
        if len(parte) < 4096:
                break
    log("Server: Bytes received: "+str(len(datos)))
    return datos

def sendData(sock,data):
    log("Server: sending "+str(len(data))+" Bytes")
    sock.sendall(data)

def sendFile(sock,filename):
    file=open(filename,"rb")
    size=os.path.getsize(filename)
    send=("file:"+str(size)).encode("utf-8")
    sock.send(send)
    log("Sending file: "+filename.name+"; Size: "+str(size)+"\n from: "+str(sock.getsockname())+" to: "+str(sock.getpeername()))
    sock.sendfile(file)
    file.close()

def sendMD5(sock,filename):
    file=open(filename,"rb")
    md5=str("MD5:"+calculatemd5(file)).encode("utf-8")
    sock.sendall(md5)
    file.close()


class ClientThread(Thread):
    def __init__(self, ip, port, socket):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.sock = socket
        self.ready = False
        self.md5=False
        self.kill = False
        log(" New thread started for "+ip+":"+str(port))

    def stop(self):
        self.kill=True

    def run(self):
        hello="Hello"
        self.sock.send(hello.encode("utf-8"))
        while True:
            data = getData(self.sock)
            message = data.decode("utf-8")
            log("Server: received message:" +message)
            if message.lower() == "exit":
                sendData(self.sock,"exit".encode("utf-8"))
                break
            elif message.lower() == "ready":
                self.ready=True
                send="Filename: "+testfile.name
                msgsend=send.encode("utf-8")
                sendData(self.sock,msgsend)
                self.md5=False
            elif message.lower() == "md5":
                self.md5=True
            if self.kill:
                break
        log("closing connection from"+str(self.ip)+":"+str(self.port))
        self.sock.close()

def sendFileToNClients(n,pFilename):
    i=0
    log("server : starting file sending test: "+str(n)+" clients; File: "+str(pFilename))
    while i<n:
        if(clients[i].ready):
            th = Thread(target=sendFile(sock=clients[i].sock,filename=pFilename))
            th.start()
            i+=1

    i=0
    while i<n:
        if(clients[i].md5):
            th = Thread(target=sendMD5(sock=clients[i].sock,filename=pFilename))
            th.start()
            i+=1
            
while True:
    client, (address,port) = server.accept()
    log("Conectado con: " + str(address) + ":" + str(port))
    newthread = ClientThread(address, port, client)
    newthread.start()
    clients.append(newthread)
    concurrentConnections += 1
    if(concurrentConnections>=int(testclients)):
        sendFileToNClients(int(testclients),testfile)
    if(concurrentConnections==-1):
        break
    log("Cantidad de clientes conectados: "+str(concurrentConnections))
server.close()