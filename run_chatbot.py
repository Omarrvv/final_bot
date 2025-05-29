#!/usr/bin/env python3
"""
Wrapper script to run the Egypt Tourism Chatbot with the correct PYTHONPATH.
"""
import os
import sys
import subprocess

# Get the current directory
current_dir = os.path.abspath(os.path.dirname(__file__))

# Set the PYTHONPATH to include the current directory
os.environ["PYTHONPATH"] = current_dir

# Instead of running the script directly, run it as a module
print(f"Starting Egypt Tourism Chatbot using 'src.main' module")
print(f"PYTHONPATH set to: {os.environ['PYTHONPATH']}")

# Run the main module
try:
    # Use the -m flag to run as a module
    subprocess.run([sys.executable, "-m", "src.main"], check=True)
except subprocess.CalledProcessError as e:
    print(f"Error running chatbot: {e}")
    sys.exit(1)
except KeyboardInterrupt:
    print("\nChatbot stopped by user.")
    sys.exit(0)
