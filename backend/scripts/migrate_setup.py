#!/usr/bin/env python
"""
Migration Setup Script

This script initializes Flask-Migrate and creates the initial migration
for the multi-tenant architecture.

Usage:
    python migrate_setup.py
"""

import os
import sys
from flask import Flask
from flask_migrate import Migrate, init, migrate, upgrade
from application import create_app, db

def setup_migrations():
    """Initialize and create database migrations"""
    app = create_app()
    
    with app.app_context():
        # Initialize migration repository if not exists
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        if not os.path.exists(migrations_dir):
            print("Initializing migration repository...")
            init()
            print("Migration repository initialized.")
        
        # Create migration
        print("\nCreating migration for multi-tenant architecture...")
        try:
            migrate(message="Multi-tenant architecture implementation")
            print("Migration created successfully.")
            print("\nReview the migration file before applying.")
            print("To apply migrations, run: flask db upgrade")
        except Exception as e:
            print(f"Error creating migration: {e}")
            return False
    
    return True

if __name__ == "__main__":
    if setup_migrations():
        print("\nMigration setup completed successfully!")
    else:
        print("\nMigration setup failed!")
        sys.exit(1)
