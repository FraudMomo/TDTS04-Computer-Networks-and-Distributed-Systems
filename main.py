import socket, re

# Constants
SERVER_PORT = 12000
CLIENT_PORT = 80
BACKLOG = 1
MAX_RECEIVE = 4096

REPLACE = {
  b'Stockholm': b'Linkoping',
  b'Smiley': b'Trolly'
}

# Create server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Allow reuse of the same port
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind(('', SERVER_PORT))
server_socket.listen(BACKLOG)

# Get connection from client
while True:
  connection_socket, addr = server_socket.accept()
  request = connection_socket.recv(MAX_RECEIVE)

  #print('Message received: ', request)

  # Extract host from request
  try:
    host = request.split(b'Host: ')[1].split(b'\r\n')[0].decode()
    print('Host: ', host)
    # Extract url from request
    url = request.split(b' ')[1].decode()
    print('URL: ', url)
  except IndexError:
    print('Invalid request')
    connection_socket.close()
    continue

  # Send request to host
  client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  client_socket.connect((host, CLIENT_PORT))
  client_socket.send(request)

  # Receive response from host
  response = b''
  while True:
    data = client_socket.recv(MAX_RECEIVE)
    if not data:
      break
    response += data
  client_socket.close()

  # Loading times can be imrpoved by using multithreading, https://www.geeksforgeeks.org/socket-programming-multi-threading-python/

  # Get status code
  status_code = response.split(b'HTTP/1.1 ')[1].split(b' ')[0].decode()
  print('Status code: ', status_code)

  if status_code in ['404', '304', '302']:
    connection_socket.send(response)
    connection_socket.close()
    continue
  
  # Return content-type recieved from host
  content_type = response.split(b'Content-Type: ')[1].split(b'\r\n')[0].decode()
  print('Content-Type: ', content_type)

  if(content_type == 'image/jpeg'):
    # If image encoded data matches the local image smiley.jpg, replace with trolly.jpg encoded data
    if(response.split(b'\r\n\r\n')[1] == open('smiley.jpg', 'rb').read()):
      print('Image encoded data matches smiley.jpg')
      response = response.replace(response.split(b'\r\n\r\n')[1], open('trolly.jpg', 'rb').read())
      # Replace content-length with new length
      response = response.replace(response.split(b'Content-Length: ')[1].split(b'\r\n')[0], str(len(response.split(b'\r\n\r\n')[1])).encode())
    else:
      print('Image encoded data does not match smiley.jpg')

  # Modify response
  modified_response = response
  
  for key, value in REPLACE.items():
    if('text/html' in content_type):
      # To replace in text but not in HTML attributes: (?<=>)[^<]+
      modified_response = re.sub(rb'(?<=>)[^<]+', lambda match: match.group().replace(key, value), modified_response)
      # To replace in alt HTML attribute (?<=(alt="))[^"]+
      modified_response = re.sub(rb'(?<=(alt="))[^"]+', lambda match: match.group().replace(key, value), modified_response)
    elif('text/plain' in content_type):
      modified_response = modified_response.replace(key, value)
  
  # Send back to client
  connection_socket.send(modified_response)
  connection_socket.close()
