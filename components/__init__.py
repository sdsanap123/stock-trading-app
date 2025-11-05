"""
Components Package

This package contains reusable UI components for the Stock Trading App.
"""

# Import the ExpandableUI class to make it available when importing from components
from .expandable_ui import ExpandableUI, ModalWindow

# Define what gets imported with 'from components import *'
__all__ = ['ExpandableUI', 'ModalWindow']
