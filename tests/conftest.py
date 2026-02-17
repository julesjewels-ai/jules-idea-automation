import sys
import os

# Add the project root directory to the Python path
# This ensures that 'src' can be imported in tests even if not installed as a package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
