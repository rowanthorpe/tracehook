#!/usr/bin/env python
# encoding: utf-8

if __package__:
  import sys, time
  from .. import tracehook as th
else:
  import os, sys, inspect, time
  trc_exec = inspect.getfile(inspect.currentframe())
  try:
    trc_exec = os.readlink(trc_exec)
  except OSError:
    pass
  trc_folder = os.path.realpath(os.path.dirname(os.path.dirname(os.path.realpath(trc_exec))))
  if trc_folder not in sys.path:
    sys.path.insert(0, trc_folder)
  del trc_exec, trc_folder
  import tracehook as th

## Just some ad-hoc testing/example usage for now...

@th.wrap()
def banana():
  time.sleep(1)
  return()

@th.wrap()
def calc(x, y, w=5, z=6):
  y = 23
  q = subcalc(1, 2)
  return(x + y, 'xxxx')

@th.wrap()
def subcalc(a, b, c="hello"):
  return(c)

@th.wrap(pre=th.no_pre, compact=True)
def calc2(x, y):
  return(x + y, [1, 2, 3])

@th.wrap(post=th.no_post)
def calc3(x, y, w=5, z=6):
  return(x + y)

@th.wrap()
def calc4(x, y, w=5, z=6):
  return(x)

@th.wrap()
def calc5(x, y, w=2, z=1):
  return(x)

@th.wrap(around=th.no_around, compact=True)
def calc6(x, y, w=7, z=8):
  return(x)

# ===

# without this the whole subsystem remains inactive/invisible
th.conf['active'] = True

# ===

th.start()

calc(3, 4, w='3')
calc2(9, 2)
calc3(7, 3, z='''
5324
223423
donkey
''')
calc4(7, 3, z=89658)
calc5(7, 3, z=[3432425324, 8])
calc6(7, 3, z={'a': 1, 'b': "trousers"})
ret_vals = calc(3, 4, w=3)

th.end(*ret_vals, compact=True)

print(ret_vals)

# ===

th.conf['col_marker'] = th.Fore.YELLOW + th.Style.BRIGHT
th.conf['col_pre'] = th.Fore.CYAN + th.Style.NORMAL
th.conf['col_pre_func'] = th.Fore.CYAN + th.Style.NORMAL
th.conf['col_around'] = th.Fore.CYAN + th.Style.NORMAL
th.conf['col_post'] = th.Fore.CYAN + th.Style.NORMAL
th.conf['col_post_func'] = th.Fore.CYAN + th.Style.NORMAL
th.conf['col_background'] = th.Fore.GREEN + th.Style.NORMAL + th.Style.DIM
th.conf['col_value'] = th.Fore.YELLOW + th.Style.NORMAL
th.conf['compact'] = True
th.conf['log'] = sys.stdout
# ...if a string is specified for 'log' it is opened as a file for output to go to

th.start(compact=True)

calc(3, 4)
calc2(9, 2)
calc3(7, 3)
calc4(7, 3)
calc5(7, 3)
calc6(7, 3)
banana()

th.end(compact=True)

print(ret_vals)

# ===

th.conf['show_markers'] = False
th.conf['indent_inc'] = 10
th.conf['col_marker'] = th.Fore.RED + th.Style.NORMAL
th.conf['col_pre'] = th.Fore.YELLOW + th.Style.NORMAL
th.conf['col_pre_func'] = th.Fore.CYAN + th.Style.NORMAL
th.conf['col_around'] = th.Fore.LIGHTBLUE_EX + th.Style.NORMAL + th.Style.DIM
th.conf['col_post'] = th.Fore.GREEN + th.Style.NORMAL
th.conf['col_post_func'] = th.Fore.MAGENTA + th.Style.NORMAL
th.conf['col_background'] = th.Fore.LIGHTBLUE_EX + th.Style.NORMAL + th.Style.DIM
th.conf['col_value'] = th.Fore.RED + th.Style.NORMAL

th.start()

calc(4000, 5000)

th.end()

# ===

th.conf['indent_inc'] = 2
th.conf['col_marker'] = th.Fore.RED + th.Style.NORMAL
th.conf['show_markers'] = True
th.conf['compact'] = False
th.conf['timestamps'] = True

th.start()

calc(3, 4)
banana()
calc4(7, 3)
ret = calc5(7, 3)

th.end(*ret_vals)

print(ret_vals)
