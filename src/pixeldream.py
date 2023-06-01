import threading
import time
import curses
import curses.textpad
import socket

server_name = "localhost"
server_port = 12000

class wins:
  def __init__(self):
    self.kill = False

    self.client_mssgs = []
    self.server_mssgs = []

    self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.connection.connect((server_name,server_port))

    self.stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    self.stdscr.clear()
    self.lock = threading.Lock()

  def reaper_has_arrived(self):
    self.connection.close()
    self.stdscr.clear()
    self.stdscr.refresh()
    curses.nocbreak()
    curses.echo()
    curses.curs_set(1)
    curses.endwin()

# TODO: TEST
def recv_mssgs(wins):
  while True:
    try:
      wins.server_mssgs.append(wins.connection.recv(1024).decode())
    except:
      break

# TODO: TEST
def delv_mssgs(wins):
  while True and wins.kill == False:
    if len(wins.client_mssgs) != 0:
      wins.lock.acquire()

      for i in wins.client_mssgs:
        wins.connection.send(i.encode())

      wins.client_mssgs.clear()
      wins.lock.release()

    time.sleep(1)

# TODO: implement server messages with actual connection
def print_mssg_thread(wins, messages_pad, from_left, lines):
  current_line = 0
  line_to_print = 0

  while True and wins.kill == False:
    if len(wins.server_mssgs) != 0:
      wins.lock.acquire()

      for i in wins.server_mssgs:
        messages_pad.addstr(i + "\n")

        if current_line > lines - 3:
          line_to_print += 1
        
        messages_pad.refresh(line_to_print, 0, 3, from_left, lines, 100)
        current_line += 1

      wins.server_mssgs.clear()
      wins.lock.release()
    time.sleep(1)

if __name__ == "__main__":
  display_name = input("Enter display name: ")

  wins = wins()

  wins.client_mssgs.append(f"{display_name} joined the chat!")

  delv_mssgs_thread = threading.Thread(target = delv_mssgs, args = (wins, ))
  recv_mssgs_thread = threading.Thread(target = recv_mssgs, args = (wins, ))

  delv_mssgs_thread.start()
  recv_mssgs_thread.start()

  stdscr = wins.stdscr
  stdscr.border()
  stdscr.refresh()

  stdscr.addstr(0, 2, f"Connected: {server_name}")
  stdscr.refresh()

  main_win_y, main_win_x = stdscr.getmaxyx()

  input_win_lines = 5
  input_win_columns = main_win_x - 4

  input_win_y = main_win_y - 8

  input_win = curses.newwin(input_win_lines, input_win_columns, input_win_y, 2)
  input_win.border()
  input_win.refresh()
  input_win.addstr(0, 2, "Say something!")
  input_win.refresh()

  input_txt_box_win_lines = input_win_lines - 2
  input_txt_box_win_columns = input_win_columns - 4
  input_txt_box_win = curses.newwin(input_txt_box_win_lines, input_txt_box_win_columns, input_win_y + 1, 4)

  users_win = curses.newwin(input_win_y - 3, input_win_y, 2, 2)
  users_win.border()
  users_win.refresh()
  users_win.addstr(0, 2, "Online")
  users_win.refresh()

  user_win_y, users_win_x = users_win.getmaxyx()

  messages_win = curses.newwin(user_win_y, input_win_columns - users_win_x - 2, 2, users_win_x + 4)
  messages_win.border()
  messages_win.refresh()
  messages_win.addstr(0, 2, "Messages")
  messages_win.refresh()

  # TODO: really should not set in stone the size of the pad, 
  # instead, should update in real time as needed
  messages_pad = curses.newpad(1000, 1000)


  print_mssg_thread = threading.Thread(target = print_mssg_thread, args = (wins, messages_pad, users_win_x + 6, user_win_y))
  print_mssg_thread.start()

  time.sleep(2)

  while True:
    user_input = ""

    while True:
      input_txt_box_win.clear()
      input_txt_box_win.addstr(user_input)

      key = input_txt_box_win.getch()

      if key == curses.KEY_RESIZE:
        stdscr.clear()

        main_win_y, main_win_x = stdscr.getmaxyx()

        stdscr.resize(main_win_y, main_win_x)
        stdscr.border()
        stdscr.refresh()

        stdscr.addstr(0, 2, "Hostname Here")
        stdscr.refresh()

        input_win_lines = 5
        input_win_columns = main_win_x - 4

        input_win_y = main_win_y - 8

        input_win.resize(input_win_lines, input_win_columns)
        input_win.mvwin(input_win_y, 2)
        input_win.border()
        input_win.refresh()
        input_win.addstr(0, 2, "Say something!")
        input_win.refresh()

        input_txt_box_win_lines = input_win_lines - 2
        input_txt_box_win_columns = input_win_columns - 4

        input_txt_box_win.resize(input_txt_box_win_lines, input_txt_box_win_columns)
        input_txt_box_win.mvwin(input_win_y + 1, 4)
        input_txt_box_win.refresh()

      cursor_y, cursor_x = input_txt_box_win.getyx()

      if key == 127:
        user_input = user_input[:-1]
      elif key == 10:
        break
      elif cursor_y != input_txt_box_win_lines - 1 or cursor_x != input_txt_box_win_columns - 1:
        user_input += chr(key)

    if user_input == "!bye":
      wins.client_mssgs.append(f"!bye {display_name}")

      time.sleep(1)
      wins.kill = True
      break
    else:
      wins.client_mssgs.append(f"{display_name}: {user_input}")


  stdscr.clear()
  stdscr.refresh()
  stdscr.addstr("Quitting...\n")
  stdscr.refresh()

  print_mssg_thread.join()
  wins.reaper_has_arrived()
