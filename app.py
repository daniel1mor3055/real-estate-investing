#!/usr/bin/env python3
"""Streamlit GUI for Real Estate Investment Analysis.

This is a thin wrapper that imports and runs the main Streamlit app
from the presentation layer.

Usage:
    streamlit run app.py
"""

from src.presentation.streamlit.app import main

if __name__ == "__main__":
    main()
