import socket
import threading
import time
import queue

QUEUE = queue.Queue(0)
PORT = 1337
LOCK = threading.Lock()

def delv_mssgs(clients):
  while True:
    mssg = QUEUE.get()

    for i in clients:
      i.send(mssg.encode())

def client_thread(conn, addr, clients):
  print(f"Connected to {addr} on port ({PORT})")
  display_name = ""

  while True:
    try:
      mssg = conn.recv(1024).decode()
    except IOError:
      break
    
    if not mssg:
      pos = clients.index(conn)
      clients.pop(pos)
      QUEUE.put(f"{display_name} left the chat!")
      break
    else:  
      if not display_name:
        display_name = mssg
        mssg += " joined the chat!"
        QUEUE.put(mssg)
      else:
        QUEUE.put(f"{display_name}: {mssg}")
        
      print(f"Received {mssg} from {addr} on port ({PORT})")

if __name__ == "__main__":
  open_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  open_socket.bind(("", PORT))
  open_socket.listen(1)

  clients = []
  delv_mssgs_thread = threading.Thread(target = delv_mssgs, args = (clients, ), daemon = True)
  delv_mssgs_thread.start()

  while True:
    try:
      conn, addr = open_socket.accept()
      clients.append(conn)
      threading.Thread(target = client_thread, args = (conn, addr, clients)).start()
    except KeyboardInterrupt:
      print("\b\bServer quit... bye!")
      break
  
  for i in clients:
    i.close()
