import threading
import time
import curses
import curses.textpad
import signal
import socket
import os
import math

def key_validator(key):
  if key == 10:
    return 7
  elif key == 127:
    return curses.KEY_BACKSPACE
  else:
    return key

def term_resize(signum, frame):
  stdscr = frame.f_locals["stdscr"]
  input_win = frame.f_locals["input_win"]
  online_win = frame.f_locals["online_win"]
  mssgs_win = frame.f_locals["mssgs_win"]

  term_x, term_y = os.get_terminal_size()

  stdscr.clear()
  curses.resizeterm(term_y, term_x)
  stdscr.border()
  stdscr.refresh()
  stdscr.addstr(0, 2, "PixelDream")
  stdscr.refresh()

  input_win.clear()
  input_win.resize(4, term_x - 8)
  input_win.mvwin(term_y - 6, 4)
  input_win.border()
  input_win.refresh()
  input_win.addstr(0, 2, "Input")
  input_win.refresh()

  online_win.clear()
  online_win.resize(term_y - 9, math.ceil(term_x / 3) - 12)
  online_win.mvwin(2, 4)
  online_win.border()
  online_win.refresh()
  online_win.addstr(0, 2, "Online")
  online_win.refresh()

  mssgs_win.clear()
  mssgs_win.resize(term_y - 9, math.ceil((term_x / 3) * 2))
  mssgs_win.mvwin(2, math.floor(term_x / 3) - 4)
  mssgs_win.border()
  mssgs_win.refresh()
  mssgs_win.addstr(0, 2, "Messages")
  mssgs_win.refresh()

  # make sure to resize the input box window

if __name__ == "__main__":
  stdscr = curses.initscr()
  curses.noecho()
  curses.cbreak()

  term_x, term_y = os.get_terminal_size()

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

  txt_box_win = curses.newwin(2, term_x - 10, term_y - 5, 5)
  txt_box = curses.textpad.Textbox(txt_box_win)

  signal.signal(signal.SIGWINCH, term_resize) 

  while True:
    txt_box_win.clear()
    txt_box.edit(key_validator)
    txt_input = txt_box.gather().strip()

    if txt_input == "!bye":
      break

  stdscr.clear()
  stdscr.refresh()
  curses.nocbreak()
  curses.echo()
  curses.curs_set(1)
  curses.endwin()
