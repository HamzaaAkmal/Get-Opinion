"""
Routes Package

This package contains all Flask blueprint route definitions for the
YouTube Scrapping application.

Blueprints:
- database_routes: Database management and statistics endpoints
- testing_routes: Health checks and testing utilities
"""

# Import blueprints for easy access
from .database_routes import database_bp
from .testing_routes import testing_bp

__all__ = ['database_bp', 'testing_bp']