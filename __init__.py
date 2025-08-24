# Workspace Python Path Configuration
# This file helps VS Code and Python tools find the correct modules
import sys
import os

# Add the src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
