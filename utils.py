import os
import sys

def restart_bot(): 
  os.execv(sys.executable, ['python3'] + sys.argv)