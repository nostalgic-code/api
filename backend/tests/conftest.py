# tests/conftest.py
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
import os
from application import create_app

@pytest.fixture
def app():
    # You can set any config overrides here for testing
    app = create_app('testing')  # or pass a config dict if your factory supports it

    # Optionally, override config for tests
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('TEST_DATABASE_URI', 'sqlite:///:memory:')
    app.config['LOGIN_DISABLED'] = True  # If you use Flask-Login

    yield app