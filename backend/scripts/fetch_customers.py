# This script fetches Customer data from the techfinity api
# And then loads the data into our customers table

import requests
import logging
from sqlalchemy.exc import SQLAlchemyError
from application import db
from application import models

# API Configuration
API_KEY = ""
API_URL = ""

# Setup Logging
logging.basicConfig(
    filename='customer_import.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)


def fetch_customer_data():
    """
    Sends a GET request to the Techfinity API to retrieve customer data.

    Returns:
        list: A list of customer records (dictionaries) from the API, 
              or an empty list if the request fails.
    """
    headers = {
        "Authorization":f"Bearer {API_KEY}"
    }

    try:
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status() # Raises an Http error if the request failed
        return response.json()
    except requests.RequestException as e:
        logging.error(f"API request failed: {e}")
        return []

def is_valid_customer(data):
    """
    Validates whether the customer data contains all required fields.

    Args:
        data (dict): A dictionary representing a single customer record.

    Returns:
        bool: True if valid, False otherwise. Logs a warning if data is incomplete.
    """
    required_fields = ['id', 'customer_code', 'name', 'email', 'phone']
    for field in required_fields:
        if field not in data or not data[field]:
            logging.warning(f"Missing required field '{field}' in customer data: {data}")
            return False
    return True

def load_customer_data():
    """
    Loads customer data from the Techfinity API into the local database.

    - Validates each customer record.
    - If a customer exists (by ID), updates their info.
    - If not, inserts them as a new record.
    - Logs every insert, update, or error.
    - Commits all successful transactions at the end.
    """
    
    customer_table = models.Customer
    customer_data = fetch_customer_data()

    if not customer_data:
        logging.info("No customer data fetched.")
        return

    success_count = 0
    error_count = 0

    for customer in customer_data:
        if not is_valid_customer(customer):
            error_count += 1
            continue

        try:
            # Check for existing customer by customer code
            existing = db.session.query(customer_table).filter_by(id=customer['id']).first()

            if existing:
                # Update existing fields
                for key, value in customer.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                logging.info(f"Updated customer ID {customer['id']}")
            else:
                # Insert new customer
                new_customer = customer_table(**customer)
                db.session.add(new_customer)
                logging.info(f"Inserted new customer ID {customer['id']}")

            success_count += 1

        except SQLAlchemyError as db_err:
            db.session.rollback()
            logging.error(f"Database error for customer ID {customer.get('id')}: {db_err}")
            error_count += 1

    try:
        db.session.commit()
        logging.info(f"Customer import completed. Success: {success_count}, Errors: {error_count}")
    except SQLAlchemyError as commit_err:
        db.session.rollback()
        logging.critical(f"Failed to commit changes: {commit_err}")

if __name__ == "__main__":
    load_customer_data()
