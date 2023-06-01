import threading
import time
import curses
import curses.textpad
import signal
import socket
import os
import math

def term_resize(signum, frame):
  stdscr = frame.f_locals["stdscr"]
  new_term_x, new_term_y = os.get_terminal_size()

  stdscr.clear()
  curses.resizeterm(new_term_y, new_term_x)
  stdscr.border()
  stdscr.refresh()
  stdscr.addstr(0, 2, "PixelDream")
  stdscr.refresh()

if __name__ == "__main__":
  stdscr = curses.initscr()
  curses.noecho()
  curses.cbreak()

  stdscr.border()
  stdscr.refresh()
  stdscr.addstr(0, 2, "PixelDream")
  stdscr.refresh()

  term_x, term_y = os.get_terminal_size()

  input_win = curses.newwin(4, term_x - 8, term_y - 6, 4)
  input_win.border()
  input_win.addstr(0, 2, "Input")
  input_win.refresh()

  input_win_maxy, input_win_maxx = input_win.getmaxyx()
  
  online_win = curses.newwin(term_y - 9, math.ceil(term_x / 3) - 12, 2, 4)
  online_win.border()
  online_win.addstr(0, 2, "Online")
  online_win.refresh()

  messages_win = curses.newwin(term_y - 9, math.ceil((term_x / 3) * 2), 2, math.floor(term_x / 3) - 4)
  messages_win.border()
  messages_win.addstr(0, 2, "Messages")
  messages_win.refresh()
  
  signal.signal(signal.SIGWINCH, term_resize) 

  time.sleep(10)

  stdscr.clear()
  stdscr.refresh()
  curses.nocbreak()
  curses.echo()
  curses.curs_set(1)
  curses.endwin()
