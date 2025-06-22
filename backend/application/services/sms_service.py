"""
SMS Service Module

Simple SMS service for sending messages via BulkSMS API.

Key Features:
- Send SMS messages using BulkSMS API
- OTP message formatting
- Error handling and logging

Classes:
    SMSService: Main SMS service class

Usage:
    from application.services.sms_service import sms_service
    success = sms_service.send_otp(phone_number, otp_code)
"""

import requests
import base64
import logging
import os
from typing import List, Union

class SMSService:
    """Simple SMS service for BulkSMS API integration."""
    
    def __init__(self):
        """Initialize SMS service with BulkSMS configuration."""
        self.api_url = "https://api.bulksms.com/v1/messages"

        # Decode and extract credentials from environment
        encoded_creds = os.getenv("BULK_SMS")
        if not encoded_creds:
            raise ValueError("BULK_SMS environment variable not set")
    
        try:
            decoded = base64.b64decode(encoded_creds).decode("utf-8")
            self.token_id, self.token_secret = decoded.split(":", 1)
        except Exception as e:
            raise ValueError("Invalid BULK_SMS credentials format") from e

        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    
    def send_otp(self, phone: str, otp: str) -> bool:
        """
        Send OTP SMS to a phone number.
        
        Args:
            phone: Phone number to send OTP to
            otp: OTP code
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        message = f"Your verification code is: {otp}\nThis code expires in 5 minutes."
        return self.send_sms(phone, message)
    
    def send_sms(self, to: Union[str, List[str]], message: str) -> bool:
        """
        Send SMS message via BulkSMS API.
        
        Args:
            to: Phone number(s) to send to (string or list)
            message: Message content
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Format phone numbers
            if isinstance(to, str):
                recipients = [self._format_phone(to)]
            else:
                recipients = [self._format_phone(phone) for phone in to]
            
            # Prepare request data
            sms_data = {
                "to": recipients,
                "body": message,
                "encoding": "UNICODE",
                "longMessageMaxParts": "30",
            }
            
            # Encode credentials
            credentials = f"{self.token_id}:{self.token_secret}"
            encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
            
            # Headers
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Basic {encoded_credentials}"
            }
            
            # Make the request
            response = requests.post(
                self.api_url,
                json=sms_data,
                headers=headers,
                timeout=30
            )
            
            # Check if successful
            response.raise_for_status()
            
            self.logger.info(f"SMS sent successfully to {recipients}")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send SMS: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Error details: {e.response.text}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending SMS: {str(e)}")
            return False
    
    def _format_phone(self, phone: str) -> str:
        """
        Format phone number for BulkSMS API.
        
        Args:
            phone: Phone number to format
            
        Returns:
            Formatted phone number
        """
        # Remove spaces and special characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Convert to international format if needed
        if phone.startswith('0'):
            # Replace leading 0 with country code (South Africa: 27)
            phone = '27' + phone[1:]
        elif not phone.startswith('27'):
            # Add country code if not present
            phone = '27' + phone
            
        return phone


# Create singleton instance
sms_service = SMSService()
