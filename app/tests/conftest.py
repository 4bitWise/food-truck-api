import os
import sys

# Add the app directory to the Python path
app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, app_path) 