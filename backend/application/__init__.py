"""
App package initialization
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def set_db(database):
    """Set the database instance"""
    global db
    db = database

__all__ = ['db', 'set_db']