import sys
import os

# Add project root to sys.path so 'src' is importable during tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
