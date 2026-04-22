"""
conftest.py — Pytest configuration for AutoStream AI tests.
Ensures the project root is on sys.path for imports.
"""

import sys
import os

# Add project root to path so tests can import agent, intent, etc.
sys.path.insert(0, os.path.dirname(__file__))
