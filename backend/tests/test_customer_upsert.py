#!/usr/bin/env python
"""
Test script for the customer upsert endpoint
This will test the endpoint we just created in the admin API
"""

import requests
import json
import sys

def test_customer_upsert():
    """Test the customer upsert endpoint"""
    
    # Test data for customer
    customer_data = {
        "customer_code": "999KJS02",
        "account_number": "999KJS02",
        "name": "KJ SPARES 4 U (PTY) LTD",
        "contact_one": "KASHIF",
        "telephone": "0725555888",
        "statement_email": "autozonehendrina@gmail.com",
        "branch_code": "999",
        "ship_via_code": "44",
        "assigned_rep": "17",
        "area_code": "009",
        "postal_address_line1": "57 KERK STREET",
        "postal_address_line2": "HENDRINA",
        "postal_address_line3": "1095",
        "street_address_line1": "27 VUYISILE MINI STREET",
        "street_address_line2": "BETHAL",
        "street_address_line3": "2310",
        "type": "company",
        "status": "on_hold",
        "created_at": "03-28-2024",
        "balance": "0.00",
        "credit_limit": "30000.00"
    }
    
    # API endpoint
    url = "https://api-2lrf.onrender.com/api/admin/customers/upsert"
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "Bearer YOUR_API_TOKEN"  # Replace with actual token if available
    }
    
    try:
        # Make the request
        print(f"Making request to: {url}")
        print(f"Request body: {json.dumps(customer_data, indent=2)}")
        
        response = requests.post(url, json=customer_data, headers=headers)
        
        # Print the response
        print(f"\nResponse status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        try:
            print(f"Response body: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response body: {response.text}")
        
        # Check if successful
        if response.status_code == 200 and response.json().get('success', False):
            print("\n✅ Test successful!")
            return True
        else:
            print("\n❌ Test failed!")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting customer upsert endpoint test...")
    print("=========================================")
    
    success = test_customer_upsert()
    
    sys.exit(0 if success else 1)
