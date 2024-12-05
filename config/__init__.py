import os
import sys

try:
    from .credentials import USERS
except ImportError:
    print("Error: credentials.py not found!")
    print("Please copy config/credentials.template.py to config/credentials.py and update with your credentials")
    sys.exit(1)

def get_credentials():
    return USERS