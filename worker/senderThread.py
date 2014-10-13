'''
Class that handles all communal communications  with the master sever
'''
import threading
from getMetrics import getPerfServer
import time
from ccmd.tools.helpers import logApp



	# this Thread will send periodically performance data about he whole instance to the master server
	# it also can be used to send messages to it or wait for its ACk messages
class senderThread(threading.Thread):
	def __init__(self, connection,frequency):
		threading.Thread.__init__(self)
		self.c = connection
		self.Terminated = False
		self.frequency = frequency
		self.nb_of_sent_msgs = 0
		
	def run(self):
		logApp("Sender thread started")
		while not self.Terminated:
			time.sleep(float(self.frequency))
			#self.c.send(  getPerfServer());
		self.c.close()
		
	def sendMsg(self,msg):
		logApp("SenderThread TX :: %s" %msg)
		self.nb_of_sent_msgs=self.nb_of_sent_msgs+1
		self.c.sendall(msg)
		
	def getAck(self):
		logApp("getAck: waiting...")
		rx = self.c.recv(1024)
		logApp("SenderThread send :: %s" %rx)
		return rx
	
	def stop(self):
		self.Terminated = True 
		logApp("SenderThread terminating #send msg %d" %self.nb_of_sent_msgs)
		
	def getNbMsg(self):
		return self.nb_of_sent_msgs
	
    
