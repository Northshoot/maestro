import socket

def send_file(connection, file):
	f_in = open(file, 'r')
	connection.sendall(f_in.read())
	connection.send('EndOfFile')
	connection.recv(len('AckFile'))
	f_in.close()

def send_str(connection, str):
	connection.sendall(str)
	connection.send('EndOfStr')
	connection.recv(len('AckStr'))
	
	
def recv_file(connection):
	result = ''
	msg = connection.recv(1024)
	while not ('EndOfStr' in msg):
		result += msg
		msg = connection.recv(1024)
	result += msg.replace('EndOfStr', '')
	connection.send('AckStr')	
	return result
	
def recv_file(connection, output_file):
	f_out = open(output_file, 'w')
	msg = connection.recv(1024)
	while not ('EndOfFile' in msg):
		f_out.write(msg)
		msg = connection.recv(1024)
	f_output.write(msg.replace('EndOfFile', ''))
	f_output.close()
	connection.send('AckFile')
