import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import and expose the required functions
from main import run as _run, stop as _stop

# Fusion 360 will call these functions
def run(context):
    print('[CoPilot] fusion_addin.py: run() called')
    return _run(context)

def stop(context):
    print('[CoPilot] fusion_addin.py: stop() called')
    return _stop(context)
