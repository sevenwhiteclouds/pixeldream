import socket
import threading
import time

PORT = 12000

class server_utility:
  def __init__(self):
    self.client = {}
    self.data = []
    self.lock = threading.Lock()

    self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.server_socket.bind(('', PORT))
    self.server_socket.listen(1)
    print("The server is ready to receive on port " + str(PORT))
    
def deliv_mssgs(utility):
  current_mssg = -1

  while True:
    if current_mssg != len(utility.data) - 1 and len(utility.data) != 0:
      current_mssg = len(utility.data) - 1

      utility.lock.acquire()

      for i in utility.client:
        utility.client[i][0].send(utility.data[current_mssg].encode())

      utility.lock.release()

    time.sleep(1)

def recv_mssgs(utility, position):
  # TODO: lol, really need to fix how long this is
  #welcome_mssg = "================================\n---Welcome to this chat room!---\n\n" + "!history -> get message history (NOT READY)\n" + "!bye -> exit and leave\n================================\n"

  #utility.client[position][0].send(welcome_mssg.encode())

  while True:
    mssg = utility.client[position][0].recv(1024).decode()
    utility.lock.acquire()
    print(f"Recieved message {mssg}")

    # TODO: change this so the client doesn't have to wait for server to close connection
    if mssg.split(" ")[0] == "!bye":
      utility.client[position][0].close()
      del utility.client[position]
      utility.data.append(mssg.split(" ")[1] + " left the chat!")
      utility.lock.release()
      break
    else:
      utility.data.append(mssg)
      utility.lock.release()

if __name__ == "__main__":
  utility = server_utility()
  threading.Thread(target = deliv_mssgs, args = (utility, )).start()

  i = 0
  while True:
    onboard_client = utility.server_socket.accept()
    utility.client[i] = [onboard_client[0], onboard_client[1]]

    threading.Thread(target = recv_mssgs, args = (utility, i)).start()

    i += 1

  server_socket.close()
