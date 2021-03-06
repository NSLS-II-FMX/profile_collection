import sys
import logging

import bluesky

import matplotlib
from IPython import get_ipython

# get_ipython().run_line_magic('matplotlib', 'widget')  # i.e. %matplotlib widget
get_ipython().run_line_magic('matplotlib', 'notebook')
import matplotlib.pyplot


# Import matplotlib and put it in interactive mode.
import matplotlib.pyplot as plt

plt.ion()

# Make plots update live while scans run.
from bluesky.utils import install_nb_kicker

install_nb_kicker()

# def isnotebook():
#     try:
#         shell = get_ipython().__class__.__name__
#         if shell == 'ZMQInteractiveShell':
#             return True   # Jupyter notebook or qtconsole
#         elif shell == 'TerminalInteractiveShell':
#             return False  # Terminal running IPython
#         else:
#             return False  # Other type (?)
#     except NameError:
#         return False      # Probably standard Python interpreter
