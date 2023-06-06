import socket
import threading
import time
import queue

QUEUE = queue.Queue(0)
PORT = 1337

def delv_mssgs(clients):
  while True:
    mssg = QUEUE.get()

    for i in clients:
      clients.send(mssg.encode())

def client_thread(conn, addr):
  print(f"Connected to {addr} on port ({PORT})")
  display_name = ""

  while True:
    mssg = conn.recv(1024).decode()

    if mssg:
      if not display_name:
        display_name = mssg
        mssg += " joined the chat!"

      QUEUE.put(mssg)
    else:
      conn.close()
      break

if __name__ == "__main__":
  open_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  open_socket.bind(("", PORT))
  open_socket.listen(1)

  clients = []
  threading.Thread(target = delv_mssgs, args = (clients, )).start()

  while True:
    conn, addr = open_socket.accept()
    clients.append(conn)
    threading.Thread(target = client_thread, args = (conn, addr)).start()
