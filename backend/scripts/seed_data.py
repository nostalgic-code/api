#!/usr/bin/env python
"""
Database Seeder Script

This script populates the database with initial data for:
- Permission codes
- Depots
- Sample customer (optional)
- Platform admin user

Usage:
    python seed_data.py
"""

from application import create_app, db
from application.models.permission_code import PermissionCode, CustomerUserRole
from application.models.depot import Depot
from application.models.customer import Customer, CustomerStatus, CustomerType
from application.models.platform_user import PlatformUser, PlatformUserRole
from werkzeug.security import generate_password_hash

def seed_permission_codes():
    """Seed default permission codes"""
    permission_codes = [
        {
            'code': 'CR101',
            'name': 'Owner Full Access',
            'role': CustomerUserRole.OWNER,
            'description': 'Full access to all features including user management',
            'default_permissions': {
                'orders': {'create': True, 'read': True, 'update': True, 'delete': True},
                'quotes': {'create': True, 'read': True, 'update': True, 'delete': True},
                'users': {'create': True, 'read': True, 'update': True, 'delete': True},
                'reports': {'view': True, 'export': True},
                'settings': {'view': True, 'update': True}
            }
        },
        {
            'code': 'CR201',
            'name': 'Staff Standard Access',
            'role': CustomerUserRole.STAFF,
            'description': 'Standard access for staff members',
            'default_permissions': {
                'orders': {'create': True, 'read': True, 'update': True, 'delete': False},
                'quotes': {'create': True, 'read': True, 'update': True, 'delete': False},
                'users': {'create': False, 'read': True, 'update': False, 'delete': False},
                'reports': {'view': True, 'export': False},
                'settings': {'view': True, 'update': False}
            }
        },
        {
            'code': 'CR301',
            'name': 'Viewer Read-Only Access',
            'role': CustomerUserRole.VIEWER,
            'description': 'Read-only access to view information',
            'default_permissions': {
                'orders': {'create': False, 'read': True, 'update': False, 'delete': False},
                'quotes': {'create': False, 'read': True, 'update': False, 'delete': False},
                'users': {'create': False, 'read': False, 'update': False, 'delete': False},
                'reports': {'view': True, 'export': False},
                'settings': {'view': False, 'update': False}
            }
        }
    ]
    
    for pc_data in permission_codes:
        existing = PermissionCode.query.filter_by(code=pc_data['code']).first()
        if not existing:
            pc = PermissionCode(**pc_data)
            db.session.add(pc)
            print(f"Created permission code: {pc_data['code']}")
    
    db.session.commit()

def seed_depots():
    """Seed depot locations"""
    depots = [
        {'code': 'JHB', 'name': 'Johannesburg Depot', 'location': 'Johannesburg'},
        {'code': 'CPT', 'name': 'Cape Town Depot', 'location': 'Cape Town'},
        {'code': 'DBN', 'name': 'Durban Depot', 'location': 'Durban'},
        {'code': 'PTA', 'name': 'Pretoria Depot', 'location': 'Pretoria'},
        {'code': 'PE', 'name': 'Port Elizabeth Depot', 'location': 'Port Elizabeth'}
    ]
    
    for depot_data in depots:
        existing = Depot.query.filter_by(code=depot_data['code']).first()
        if not existing:
            depot = Depot(**depot_data)
            db.session.add(depot)
            print(f"Created depot: {depot_data['code']}")
    
    db.session.commit()

def seed_platform_admin():
    """Create initial platform admin user"""
    admin_email = 'admin@platform.com'
    existing = PlatformUser.query.filter_by(email=admin_email).first()
    
    if not existing:
        admin = PlatformUser(
            name='Platform Administrator',
            email=admin_email,
            phone='+27123456789',  # Update with real phone
            password=generate_password_hash('changeme123'),  # Change in production
            role=PlatformUserRole.ADMIN
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Created platform admin: {admin_email}")
        print("Default password: changeme123 (PLEASE CHANGE THIS!)")

def seed_sample_customer():
    """Create a sample customer for testing"""
    customer_code = 'CUST001'
    existing = Customer.query.filter_by(customer_code=customer_code).first()
    
    if not existing:
        customer = Customer(
            customer_code=customer_code,
            account_number='ACC001',
            name='Sample Company Ltd',
            type=CustomerType.COMPANY,
            status=CustomerStatus.APPROVED
        )
        db.session.add(customer)
        db.session.commit()
        print(f"Created sample customer: {customer_code}")

def main():
    """Run all seeders"""
    app = create_app()
    
    with app.app_context():
        print("Starting database seeding...")
        
        print("\n1. Seeding permission codes...")
        seed_permission_codes()
        
        print("\n2. Seeding depots...")
        seed_depots()
        
        print("\n3. Creating platform admin...")
        seed_platform_admin()
        
        print("\n4. Creating sample customer...")
        seed_sample_customer()
        
        print("\nDatabase seeding completed!")

if __name__ == "__main__":
    main()
