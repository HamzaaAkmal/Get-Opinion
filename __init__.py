"""
YouTube Scrapping Application Package

A professional, modular Flask application for scraping and analyzing
YouTube and Reddit comments with AI-powered query generation.

Version: 2.1 - Modern Modular Architecture
"""

__version__ = "2.1"
__author__ = "YouTube Scrapping Team"
__description__ = "AI-powered YouTube and Reddit comment scraping application"

# Package metadata
__all__ = [
    'create_app',
    'main'
]

from application import create_app