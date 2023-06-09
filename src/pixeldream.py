import threading
import time
import signal
import curses
import curses.textpad
import socket
import math
import queue

SERVER = "localhost"
PORT = 1337
QUEUE_RECV = queue.Queue(0)
QUEUE_SEND = queue.Queue(0)
QUEUE_ONLINE = queue.Queue(0)

class Textbox(curses.textpad.Textbox):
  def __init__(self, win, stdscr, online_win, mssgs_win, input_win, mssgs_pad, insert_mode=False):
    self.win = win
    self.insert_mode = insert_mode
    self._update_max_yx()
    self.stripspaces = 1
    self.lastcmd = None
    win.keypad(1)

    # extending Textbox class for custom variables for resizing
    self.stdscr = stdscr
    self.online_win = online_win
    self.mssgs_win = mssgs_win
    self.input_win = input_win
    self.mssgs_pad = mssgs_pad

  def term_resize(self):
    term_y, term_x = self.stdscr.getmaxyx()

    self.stdscr.clear()
    curses.resizeterm(term_y, term_x)
    self.stdscr.border()
    self.stdscr.refresh()
    self.stdscr.addstr(0, 2, "PixelDream")
    self.stdscr.refresh()

    self.input_win.clear()
    self.input_win.resize(4, term_x - 8)
    self.input_win.mvwin(term_y - 6, 4)
    self.input_win.border()
    self.input_win.refresh()
    self.input_win.addstr(0, 2, "Input")
    self.input_win.refresh()

    self.online_win.clear()
    self.online_win.resize(term_y - 9, math.ceil(term_x / 3) - 12)
    self.online_win.mvwin(2, 4)
    self.online_win.border()
    self.online_win.refresh()
    self.online_win.addstr(0, 2, "Online")
    self.online_win.refresh()

    # TODO: logic for online users has not been written, check thread func
    # and constructor also needs to be updated
    #self.online_pad.resize(1000, math.ceil(term_x / 3) - 12)
    #self.online_win.refresh()

    self.mssgs_win.clear()
    self.mssgs_win.resize(term_y - 9, math.ceil((term_x / 3) * 2))
    self.mssgs_win.mvwin(2, math.floor(term_x / 3) - 4)
    self.mssgs_win.border()
    self.mssgs_win.refresh()
    self.mssgs_win.addstr(0, 2, "Messages")
    self.mssgs_win.refresh()

    self.mssgs_pad.resize(1000, math.ceil(((term_x / 3) * 2 - 2)))
    self.mssgs_win.refresh()

    # TODO: the 3 lines below resize the win while keeping 
    # what the user typed but it doesn't auto extend
    # the text if new resolution is longer than before
    # what is worse, text gets lost if the new resolution is shorter in width.
    self.win.resize(2, term_x - 10)
    self.win.mvwin(term_y - 5, 5)
    self.win.refresh()

  def do_command(self, ch):
    # extending Textbox class, checking to see if we are resizing
    if ch == curses.KEY_RESIZE:
      self.term_resize()

    "Process a single editing command."
    self._update_max_yx()
    (y, x) = self.win.getyx()
    self.lastcmd = ch

    if curses.ascii.isprint(ch):
      if y < self.maxy or x < self.maxx:
        self._insert_printable_char(ch)
    elif ch == curses.ascii.SOH:                           # ^a
      self.win.move(y, 0)
    elif ch in (curses.ascii.STX,curses.KEY_LEFT,
                curses.ascii.BS,
                curses.KEY_BACKSPACE,
                curses.ascii.DEL, 127):
      if x > 0:
        self.win.move(y, x-1)
      elif y == 0:
        pass
      elif self.stripspaces:
        self.win.move(y-1, self._end_of_line(y-1))
      else:
        self.win.move(y-1, self.maxx)
      if ch in (curses.ascii.BS, curses.KEY_BACKSPACE, curses.ascii.DEL, 127):
        self.win.delch()
    elif ch == curses.ascii.EOT:                           # ^d
      self.win.delch()
    elif ch == curses.ascii.ENQ:                           # ^e
      if self.stripspaces:
        self.win.move(y, self._end_of_line(y))
      else:
        self.win.move(y, self.maxx)
    elif ch in (curses.ascii.ACK, curses.KEY_RIGHT):       # ^f
      if x < self.maxx:
        self.win.move(y, x+1)
      elif y == self.maxy:
        pass
      else:
        self.win.move(y+1, 0)
    elif ch == curses.ascii.BEL or ch == 10:               # ^g
      return 0
    elif ch == curses.ascii.NL:                            # ^j
      if self.maxy == 0:
        return 0
      elif y < self.maxy:
        self.win.move(y+1, 0)
    elif ch == curses.ascii.VT:                            # ^k
      if x == 0 and self._end_of_line(y) == 0:
        self.win.deleteln()
      else:
        # first undo the effect of self._end_of_line
        self.win.move(y, x)
        self.win.clrtoeol()
    elif ch == curses.ascii.FF:                            # ^l
      self.win.refresh()
    elif ch in (curses.ascii.SO, curses.KEY_DOWN):         # ^n
      if y < self.maxy:
        self.win.move(y+1, x)
        if x > self._end_of_line(y+1):
          self.win.move(y+1, self._end_of_line(y+1))
    elif ch == curses.ascii.SI:                            # ^o
      self.win.insertln()
    elif ch in (curses.ascii.DLE, curses.KEY_UP):          # ^p
      if y > 0:
        self.win.move(y-1, x)
        if x > self._end_of_line(y-1):
          self.win.move(y-1, self._end_of_line(y-1))
    return 1

def get_fserver(conn):
  while True:
    try:
      # TODO: handle server disconnects with a "not mssg"
      mssg = conn.recv(1024).decode()

      if "joined the chat!" in mssg:  
        online_up = mssg.split(" ")
        QUEUE_ONLINE.put(online_up)
      elif "left the chat!" in mssg:
        online_up = mssg.split(" ")
        QUEUE_ONLINE.put(online_up)
      else:
        QUEUE_RECV.put(mssg)

    # user is trying to quit
    except IOError:
      break

def push_tserver(conn):
  while True:
    try:
      mssg = QUEUE_SEND.get()
      conn.send(mssg.encode())
    # ioerror here would mean that user is trying to quit
    except IOError:
      break

# TODO: write logic for online users
def online_thread(online_pad, online_win, stdscr):
  while True:
    time.sleep(.25)

    term_y, term_x = stdscr.getmaxyx()
    y, x = online_win.getmaxyx()
    #x += math.floor(term_x / 3) - 6
    y_cursor, x_cursor = online_pad.getyx()

    # perhaps the solution to the TODO above is something similar to this but for the x value?
    if (y_cursor - y) < -2:
      scroll = 0
    else:
      scroll = (y_cursor - y) + 3

    try:
      mssg = QUEUE_ONLINE.get_nowait()
    except queue.Empty:
      continue
    else:
      if mssg[1] == "joined":
        online_pad.addstr(f"{mssg[0]}\n")
      else:
        online_pad.addstr(f"yup\n")
    finally:
      online_pad.refresh(scroll, 0, 3, 5, y, x)

# TODO: text wrap partially works, the only issue
# now is that text doesn't extend if new res is greater in width than previous
def mssgs_thread(mssgs_pad, mssgs_win, stdscr):
  while True:
    time.sleep(.25)

    term_y, term_x = stdscr.getmaxyx()
    y, x = mssgs_win.getmaxyx()
    x += math.floor(term_x / 3) - 6
    y_cursor, x_cursor = mssgs_pad.getyx()

    # perhaps the solution to the TODO above is something similar to this but for the x value?
    if (y_cursor - y) < -2:
      scroll = 0
    else:
      scroll = (y_cursor - y) + 3

    try:
      mssg = QUEUE_RECV.get_nowait()
    except queue.Empty:
      continue
    else:
      mssgs_pad.addstr(f"{mssg}\n")
    finally:
      mssgs_pad.refresh(scroll, 0, 3, math.floor(term_x / 3) - 3, y, x)

if __name__ == "__main__":
  display_name = input("Enter display name: ")
  QUEUE_SEND.put(display_name)

  conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  conn.connect((SERVER, PORT))

  stdscr = curses.initscr()
  curses.cbreak()
  curses.noecho()
  curses.curs_set(0)

  term_y, term_x = stdscr.getmaxyx()

  stdscr.border()
  stdscr.refresh()
  stdscr.addstr(0, 2, "PixelDream")
  stdscr.refresh()

  input_win = curses.newwin(4, term_x - 8, term_y - 6, 4)
  input_win.border()
  input_win.addstr(0, 2, "Input")
  input_win.refresh()

  online_win = curses.newwin(term_y - 9, math.ceil(term_x / 3) - 12, 2, 4)
  online_win.border()
  online_win.addstr(0, 2, "Online")
  online_win.refresh()

  mssgs_win = curses.newwin(term_y - 9, math.ceil((term_x / 3) * 2), 2, math.floor(term_x / 3) - 4)
  mssgs_win.border()
  mssgs_win.addstr(0, 2, "Messages")
  mssgs_win.refresh()

  push_tserver_thread = threading.Thread(target = push_tserver, args = (conn, ), daemon = True)
  push_tserver_thread.start()

  get_fserver_thread = threading.Thread(target = get_fserver, args = (conn, ), daemon = True)
  get_fserver_thread.start()

  # TODO: change 1000 lines, not good to hard code like this. ok for now.
  # once this hard coding is fixed, also make sure to fix in the resizing
  # this also applies the mssgs_pad below.
  online_pad = curses.newpad(1000, math.ceil(term_x / 3) - 14)
  online_thread = threading.Thread(target = online_thread, args = (online_pad, online_win, stdscr), daemon = True)
  online_thread.start()

  mssgs_pad = curses.newpad(1000, math.ceil(((term_x / 3) * 2 - 2)))
  # since this thread doesn't block, killing with daemon status (not like the others)
  mssgs_thread = threading.Thread(target = mssgs_thread, args = (mssgs_pad, mssgs_win, stdscr, ), daemon = True)
  mssgs_thread.start()

  txt_box_win = curses.newwin(2, term_x - 10, term_y - 5, 5)
  txt_box = Textbox(txt_box_win, stdscr, online_win, mssgs_win, input_win, mssgs_pad, )

  time.sleep(1)
  while True:
    txt_box_win.clear()
    txt_input = txt_box.edit().strip()

    if txt_input == "!bye":
      conn.close()
      break
    else:
      QUEUE_SEND.put(txt_input)

  stdscr.clear()
  stdscr.refresh()
  curses.nocbreak()
  curses.echo()
  curses.curs_set(1)
  curses.endwin()
