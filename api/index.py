import sys
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(base_dir)

for p in [parent_dir, base_dir]:
    if p and p not in sys.path:
        sys.path.insert(0, p)

from app import app
