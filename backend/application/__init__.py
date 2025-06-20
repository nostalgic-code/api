"""
Application Package Initialization

This module initializes the Flask application components and makes
the database instance available to all modules.
"""

from flask_sqlalchemy import SQLAlchemy

# Initialize database instance
db = SQLAlchemy()

# Make commonly used imports available at package level
from .utils.database import DatabaseConnection

__all__ = ['db', 'DatabaseConnection']