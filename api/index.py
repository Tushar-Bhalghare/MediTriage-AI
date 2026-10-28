import sys
import os

# Add parent directory to path so app.py and templates are found
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app import app

# Vercel WSGI entrypoint
app.debug = False
