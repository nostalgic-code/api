"""
Frontend Routes Module

Serves frontend HTML files for the multi-tenant system.
"""

from flask import Blueprint, send_from_directory, redirect
import os

# Create Blueprint
frontend_bp = Blueprint('frontend', __name__)

# Get the frontend directory path
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../frontend'))

@frontend_bp.route('/')
def index():
    """Redirect to login page"""
    return redirect('/auth/login')

@frontend_bp.route('/auth/<path:filename>')
def serve_auth(filename):
    """Serve authentication pages"""
    # Add .html extension if not present
    if not filename.endswith('.html'):
        filename += '.html'
    return send_from_directory(os.path.join(FRONTEND_DIR, 'auth'), filename)

@frontend_bp.route('/admin/<path:filename>')
def serve_admin(filename):
    """Serve admin pages and assets"""
    # Handle the dashboard route mapping
    if filename == 'dashboard':
        filename = 'admin-dashboard.html'
        return send_from_directory(os.path.join(FRONTEND_DIR, 'admin'), filename)
    
    # Handle JavaScript files (including those in js/ subdirectory)
    if filename.endswith('.js') or filename.startswith('js/'):
        return send_from_directory(os.path.join(FRONTEND_DIR, 'admin'), filename)
    
    # Handle component files (HTML files in components directory)
    if filename.startswith('components/') and filename.endswith('.html'):
        return send_from_directory(os.path.join(FRONTEND_DIR, 'admin'), filename)
    
    # Handle CSS files
    if filename.endswith('.css') or filename.startswith('assets/'):
        return send_from_directory(os.path.join(FRONTEND_DIR, 'admin'), filename)
    
    # Handle regular HTML files
    if not filename.endswith('.html'):
        filename += '.html'
    return send_from_directory(os.path.join(FRONTEND_DIR, 'admin'), filename)

@frontend_bp.route('/customer/<path:filename>')
def serve_customer(filename):
    """Serve customer pages"""
    # Handle common mappings
    if filename == 'home':
        filename = 'customer-dashboard'
    
    if not filename.endswith('.html'):
        filename += '.html'
    return send_from_directory(os.path.join(FRONTEND_DIR, 'customer'), filename)

# Legacy route support
@frontend_bp.route('/dashboard')
def legacy_dashboard():
    """Serve the legacy dashboard"""
    return send_from_directory(os.path.join(FRONTEND_DIR, 'static'), 'dashboard.html')