"""
Run Anu Dashboard in the background.
This script has a .pyw extension so it runs without showing a console window.
"""

import os
import sys
import subprocess
import time

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the main Anu Dashboard script
    anu_script = os.path.join(script_dir, "anu_dashboard.py")
    
    # Start Anu Dashboard using pythonw (no console window)
    subprocess.Popen([sys.executable, anu_script], 
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    cwd=script_dir)

if __name__ == "__main__":
    # Add a small delay to ensure system is fully loaded
    time.sleep(5)
    main()