import threading
import time
import curses
import curses.textpad
import signal
import socket
import os

def term_resize(signum, frame):
  stdscr = frame.f_locals["stdscr"]
  new_win_x, new_win_y= os.get_terminal_size()

  stdscr.clear()
  curses.resizeterm(new_win_y, new_win_x)
  stdscr.border()
  stdscr.refresh()

if __name__ == "__main__":
  stdscr = curses.initscr()
  curses.noecho()
  curses.cbreak()
  
  stdscr.border()
  stdscr.refresh()

  signal.signal(signal.SIGWINCH, term_resize) 

  time.time(10)

  stdscr.clear()
  stdscr.refresh()
  curses.nocbreak()
  curses.echo()
  curses.curs_set(1)
  curses.endwin()
