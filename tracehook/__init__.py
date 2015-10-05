# encoding: utf-8

# tracehook
#
# (c) 2015 Rowan Thorpe
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys, inspect, pprint, time
try:
  from collections import OrderedDict
except(ImportError): # python < 2.6 needs this
  OrderedDict = dict
from colorama import Fore, Back, Style
from io import open

__version__ = '0.3.2'

global conf, state

# Editable defaults
conf = {}
conf['active'] = False
conf['log'] = sys.stderr
conf['compact'] = False
conf['indent_inc'] = 2
conf['show_markers'] = True
conf['timestamps'] = False
# NB: Style.NORMAL seems to be needed before BRIGHT or DIM to unset their
#     opposites first... (e.g. DIM --then--> NORMAL + BRIGHT)
conf['col_marker'] = Fore.RED + Style.NORMAL
conf['col_pre'] = Fore.YELLOW + Style.NORMAL
conf['col_pre_func'] = Fore.CYAN + Style.NORMAL
conf['col_around'] = Fore.LIGHTBLUE_EX + Style.NORMAL + Style.DIM
conf['col_post'] = Fore.GREEN + Style.NORMAL
conf['col_post_func'] = Fore.MAGENTA + Style.NORMAL
conf['col_background'] = Fore.LIGHTBLUE_EX + Style.NORMAL + Style.DIM
conf['col_kwargname'] = Fore.BLUE + Style.NORMAL + Style.BRIGHT
conf['col_argname'] = Fore.GREEN + Style.NORMAL + Style.DIM
conf['col_value'] = Fore.RED + Style.NORMAL
conf['col_reset'] = Style.RESET_ALL
state = {
  'started': False,
  'tracing': None,
  'traced_locals': None,
  'start_time': None,
  'opened_log': None,
  'timestamp_size': None,
  'indent': None,
  'last_was': None,
  'log': None,
}

def trace_snapshot_at_return(frame, event, arg):
  if frame.f_code.co_name == state['tracing'] and event == 'return':
    state['traced_locals'] = frame.f_locals
    return
  return(trace_snapshot_at_return)

def timestamp():
  return("{:0>12} ".format('%.6f' % (time.time() - state['start_time'])))

def start(**kwargs):
  if conf['active']:
    if(state['started']):
      raise RuntimeError('Already started.')
    else:
      state['started'] = True
    try:
      compact = kwargs['compact']
    except(KeyError):
      compact = conf['compact']
    state['indent'] = 0
    state['last_was'] = 'pre'

    try:
      basestring
    except(NameError):
      basestring = str
    if isinstance(conf['log'], basestring):
      state['log'] = open(conf['log'], 'a', encoding='utf-8')
      state['opened_log_file'] = True
    else:
      state['log'] = conf['log']
      state['opened_log_file'] = False
    try:
      sep = sys.argv.index("--")
    except(ValueError):
      sep = None
    try:
      optargs = sys.argv[1:sep]
      args = sys.argv[sep + 1:]
    except(TypeError):
      optargs = sys.argv[1:]
      args = []
    if conf['timestamps']:
      state['timestamp_size'] = 13
      state['start_time'] = time.time()

    if conf['show_markers']:
      state['log'].write("{}====> DEBUG STARTS HERE\n".format(conf['col_marker']))
    if conf['timestamps']:
        state['log'].write(conf['col_background'] + timestamp())
    state['log'].write("{} ->{}__main__{}(".format(conf['col_pre'], conf['col_pre_func'], conf['col_pre']))
    state['log'].write(
      "{}, ".format(conf['col_background']).join(
        [
         ["{}{}".format(conf['col_value'], x), "{}{}".format(conf['col_argname'], x)][x[0:2] == "--"] for x in optargs] +
        [[], ["{}--".format(conf['col_background'])]][sep is not None] +
        ["{}{}".format(conf['col_value'], x) for x in args]
      ) +
      "{})\n".format(conf['col_pre'])
    )
    if not compact:
      if conf['timestamps']:
        state['log'].write(" " * state['timestamp_size'])
      state['log'].write(conf['col_background'] + ("|" + " " * conf['indent_inc']) * state['indent'] + "/\n")

    state['log'].write(conf['col_reset'])

def end(*ret_vals, **kwargs):
  if conf['active']:
    if(not state['started']):
      raise RuntimeError('Not started.')
    try:
      compact = kwargs['compact']
    except(KeyError):
      compact = conf['compact']

    if not compact:
      if conf['timestamps']:
        state['log'].write(" " * state['timestamp_size'])
      state['log'].write(conf['col_background'] + ("|" + " " * conf['indent_inc']) * state['indent'] + "\\\n")
    if conf['timestamps']:
        state['log'].write(conf['col_background'] + timestamp())
    state['log'].write("{} <-{}__main__{}(".format(conf['col_post'], conf['col_post_func'], conf['col_post']))
    state['log'].write(
      "{}, ".format(conf['col_background']).join(
        "{}{}".format(conf['col_value'], repr(ret_val).replace("\n", " ")) for ret_val in ret_vals
      )
    )
    state['log'].write("{})\n".format(conf['col_post']))
    if conf['show_markers']:
      state['log'].write("{}====> DEBUG ENDS HERE\n".format(conf['col_marker']))

    state['timestamp_size'] = None
    state['start_time'] = None
    state['log'].write(conf['col_reset'])
    state['log'].flush()
    if state['opened_log_file']:
      state['log'].close()
      state['log'] = None
      state['opened_log_file'] = None
    state['started'] = False

def pre(func, args, kwargs, func_name, arg_dict, kw_dict, compact):
  if conf['active']:
    if(not state['started']):
      raise RuntimeError('Not started.')
    state['indent'] += 1

    if not conf['compact'] and (state['last_was'] != 'pre'): # test *global* "compact" here
      if conf['timestamps']:
        state['log'].write(" " * state['timestamp_size'])
      state['log'].write(conf['col_background'] + ("|" + " " * conf['indent_inc']) * state['indent'] + "\n")
    if conf['timestamps']:
        state['log'].write(conf['col_background'] + timestamp())
    state['log'].write(
      conf['col_background'] + ("|" + " " * conf['indent_inc']) * state['indent'] +
      "{} -->{}{}{}(".format(conf['col_pre'], conf['col_pre_func'], func_name, conf['col_pre'])
    )
    to_iterate = [
      "{}{} {}= {}{}".format(
        conf['col_argname'], x, conf['col_background'], conf['col_value'], repr(arg_dict[x])
      ) for x in arg_dict
    ]
    for x in kw_dict:
      to_iterate.append("{}{} {}= {}{}".format(conf['col_kwargname'], x, conf['col_background'], conf['col_value'], repr(kw_dict[x]['val'])))
      if kw_dict[x]['val'] == kw_dict[x]['default']:
        to_iterate[-1] += "{}(default)".format(conf['col_background'])
    state['log'].write("{}, ".format(conf['col_background']).join(to_iterate))
    state['log'].write("{})\n".format(conf['col_pre']))
    if not compact:
      if conf['timestamps']:
        state['log'].write(" " * state['timestamp_size'])
      state['log'].write(conf['col_background'] + ("|" + " " * conf['indent_inc']) * state['indent'] + "/\n")

    state['log'].write(conf['col_reset'])
    state['last_was'] = 'pre'

def no_pre(func, args, kwargs, func_name, arg_dict, kw_dict, compact):
  if conf['active']:
    if(not state['started']):
      raise RuntimeError('Not started.')
    state['indent'] += 1

    if not conf['compact'] and (state['last_was'] != 'pre'): # test *global* compact here
      if conf['timestamps']:
        state['log'].write(" " * state['timestamp_size'])
      state['log'].write(conf['col_background'] + ("|" + " " * conf['indent_inc']) * state['indent'] + "\n")

    state['log'].write(conf['col_reset'])
    state['last_was'] = 'pre'

def around(func, args, kwargs, func_name, compact):
  if conf['active']:
    if(not state['started']):
      raise RuntimeError('Not started.')

    state['tracing'] = func_name
    sys.settrace(trace_snapshot_at_return)
    ret_vals = func(*args, **kwargs)
    sys.settrace(None)
    state['tracing'] = None

    if not compact and (state['last_was'] == 'post'):
      if conf['timestamps']:
        state['log'].write(" " * state['timestamp_size'])
      state['log'].write(conf['col_background'] + ("|" + " " * conf['indent_inc']) * state['indent'] + "|\n")
    if conf['timestamps']:
      state['log'].write(conf['col_background'] + timestamp())
    state['log'].write(
      conf['col_background'] + ("|" + " " * conf['indent_inc']) * state['indent'] +
      "|-->{}{}{}(".format(conf['col_pre_func'], func_name, conf['col_background'])
    )
    if state['traced_locals']:
      state['log'].write(
        "{}, ".format(conf['col_background']).join(
          "{}{} {}= {}{}".format(conf['col_argname'], key, conf['col_background'], conf['col_value'],
            pprint.saferepr(state['traced_locals'][key])
          ) for key in state['traced_locals']
        )
      )
      state['traced_locals'] = None
    state['log'].write("{})\n".format(conf['col_background']))

    state['log'].write(conf['col_reset'])
    state['last_was'] = 'around'
    return(ret_vals)

def no_around(func, args, kwargs, func_name, compact):
  if conf['active']:
    if(not state['started']):
      raise RuntimeError('Not started.')

    state['last_was'] = 'around'

def post(func, args, kwargs, func_name, ret_vals, compact):
  if conf['active']:
    if(not state['started']):
      raise RuntimeError('Not started.')

    if not compact:
      if conf['timestamps']:
        state['log'].write(" " * state['timestamp_size'])
      state['log'].write(conf['col_background'] + ("|" + " " * conf['indent_inc']) * state['indent'] + "\\\n")
    if conf['timestamps']:
      state['log'].write(conf['col_background'] + timestamp())
    state['log'].write(
      conf['col_background'] + ("|" + " " * conf['indent_inc']) * state['indent'] +
      "{} <--{}{}{}(".format(conf['col_post'], conf['col_post_func'], func_name, conf['col_post'])
    )
    if ret_vals is None:
      state['log'].write(") {}<empty>\n".format(conf['col_background']))
    elif hasattr(ret_vals, "__iter__"):
      state['log'].write(
        "{}, ".format(conf['col_background']).join(
          "{}{}".format(conf['col_value'], repr(ret_val).replace("\n", " ")) for ret_val in ret_vals
        ) +
        "{}) {}{}\n".format(
          conf['col_post'], conf['col_background'], type(ret_vals)
        )
      )
    else:
      state['log'].write(
        "{}{}".format(conf['col_value'], repr(ret_vals)) +
        "{}) {}{}\n".format(conf['col_post'], conf['col_background'], type(ret_vals))
      )

    state['log'].write(conf['col_reset'])
    state['indent'] -= 1
    state['last_was'] = 'post'

def no_post(func, args, kwargs, func_name, ret_vals, compact):
  if conf['active']:
    if(not state['started']):
      raise RuntimeError('Not started.')

    if not compact:
      if conf['timestamps']:
        state['log'].write(" " * state['timestamp_size'])
      state['log'].write(conf['col_background'] + ("|" + " " * conf['indent_inc']) * state['indent'] + "\n")

    state['log'].write(conf['col_reset'])
    state['indent'] -= 1
    state['last_was'] = 'post'

def wrap(pre=pre, around=around, post=post, compact=None):
  def decorate(func):
    def call(*args, **kwargs):
      func_name = func.__name__
      argspec = inspect.getargspec(func)
      callargs = inspect.getcallargs(func, *args, **kwargs)
      try:
        kw_num= len(argspec.defaults)
      except(AttributeError, TypeError):
        kw_num = 0
      arg_num = len(argspec.args) - kw_num
      arg_dict = OrderedDict()
      kw_dict = OrderedDict()
      for x in range(arg_num):
        arg_name = argspec.args[x]
        arg_dict[arg_name] = callargs[arg_name]
      for x in range(kw_num):
        kw_name = argspec.args[arg_num + x]
        kw_dict[kw_name] = {'default': argspec.defaults[x], 'val': callargs[kw_name]}
      if compact is None:
        pre(func, args, kwargs, func_name, arg_dict, kw_dict, conf['compact'])
        ret_vals = around(func, args, kwargs, func_name, conf['compact'])
        post(func, args, kwargs, func_name, ret_vals, conf['compact'])
      else:
        pre(func, args, kwargs, func_name, arg_dict, kw_dict, compact)
        ret_vals = around(func, args, kwargs, func_name, compact)
        post(func, args, kwargs, func_name, ret_vals, compact)
      return(ret_vals)
    return(call)
  return(decorate)
