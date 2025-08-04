"""
API Client Service

A service for making API calls to external systems.

This client handles authentication, request formatting, and response parsing
for all external API interactions.

Author: Development Team
Version: 1.0
"""

import requests
import logging
import json
import os
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class ApiClient:
    """
    API Client for making requests to external systems
    
    Attributes:
        base_url (str): Base URL for API requests
        headers (dict): Default headers for all requests
    """
    
    def __init__(self, base_url=None):
        """
        Initialize the API client
        
        Args:
            base_url (str, optional): Base URL for API requests. Defaults to environment variable.
        """
        self.base_url = base_url or os.environ.get('API_BASE_URL', 'https://api.example.com')
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Add authentication header if available
        api_key = os.environ.get('API_KEY')
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
            
        # ERP API specific settings
        self.erp_api_url = os.environ.get('ERP_API_URL', 'http://102.33.60.228:9183')
        self.erp_api_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _build_url(self, endpoint):
        """
        Build a full URL from the endpoint
        
        Args:
            endpoint (str): API endpoint path
            
        Returns:
            str: Full URL
        """
        # Remove leading slash if present
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]
        
        return urljoin(self.base_url, endpoint)
    
    def _handle_response(self, response):
        """
        Handle API response and convert to dict
        
        Args:
            response (Response): Requests Response object
            
        Returns:
            dict: Response data
            
        Raises:
            Exception: If response contains an error
        """
        try:
            data = response.json()
            
            if response.status_code >= 400:
                error_msg = data.get('message', data.get('error', 'Unknown error'))
                logger.error(f"API error ({response.status_code}): {error_msg}")
                return {
                    'success': False,
                    'message': error_msg,
                    'status_code': response.status_code
                }
                
            return data
            
        except ValueError:
            logger.error(f"Invalid JSON response: {response.text}")
            return {
                'success': False,
                'message': 'Invalid response format',
                'status_code': response.status_code
            }
    
    def get(self, endpoint, params=None):
        """
        Make a GET request
        
        Args:
            endpoint (str): API endpoint
            params (dict, optional): Query parameters
            
        Returns:
            dict: Response data
        """
        url = self._build_url(endpoint)
        logger.debug(f"GET request to {url}")
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Error making GET request to {url}: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def post(self, endpoint, data):
        """
        Make a POST request
        
        Args:
            endpoint (str): API endpoint
            data (dict): Request payload
            
        Returns:
            dict: Response data
        """
        url = self._build_url(endpoint)
        logger.debug(f"POST request to {url}")
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Error making POST request to {url}: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def put(self, endpoint, data):
        """
        Make a PUT request
        
        Args:
            endpoint (str): API endpoint
            data (dict): Request payload
            
        Returns:
            dict: Response data
        """
        url = self._build_url(endpoint)
        logger.debug(f"PUT request to {url}")
        
        try:
            response = requests.put(url, headers=self.headers, json=data)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Error making PUT request to {url}: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def delete(self, endpoint, params=None):
        """
        Make a DELETE request
        
        Args:
            endpoint (str): API endpoint
            params (dict, optional): Query parameters
            
        Returns:
            dict: Response data
        """
        url = self._build_url(endpoint)
        logger.debug(f"DELETE request to {url}")
        
        try:
            response = requests.delete(url, headers=self.headers, params=params)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Error making DELETE request to {url}: {str(e)}")
            return {'success': False, 'message': str(e)}
            
    def call_erp_api(self, endpoint, data):
        """
        Make a POST request to the ERP API
        
        Args:
            endpoint (str): API endpoint (relative to ERP API base URL)
            data (dict): Request payload
            
        Returns:
            dict: Response data with standardized format
        """
        # Remove leading slash if present
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]
            
        url = f"{self.erp_api_url}/{endpoint}"
        logger.info(f"Calling ERP API: POST {url}")
        logger.debug(f"ERP API payload: {json.dumps(data)}")
        
        try:
            response = requests.post(url, headers=self.erp_api_headers, json=data)
            
            # Log the raw response for debugging
            logger.debug(f"ERP API raw response: {response.text}")
            
            try:
                result = response.json()
                
                # Handle ERP API specific response format
                if 'response' in result:
                    erp_response = result['response']
                    success = erp_response.get('Success') == "0000"
                    message = erp_response.get('Message', '')
                    
                    # Extract P-number from success message if available
                    p_number = None
                    if success and 'reference [P' in message and ']' in message:
                        p_number_start = message.find('[P') + 2
                        p_number_end = message.find(']', p_number_start)
                        if p_number_start > 0 and p_number_end > p_number_start:
                            p_number = 'P' + message[p_number_start:p_number_end]
                    
                    return {
                        'success': success,
                        'message': message,
                        'data': {
                            'p_number': p_number,
                            'raw_response': result
                        }
                    }
                
                # Default handling if not in expected format
                return {
                    'success': response.status_code < 400,
                    'message': 'Unexpected response format from ERP API',
                    'data': result
                }
                
            except ValueError:
                logger.error(f"Invalid JSON response from ERP API: {response.text}")
                return {
                    'success': False,
                    'message': 'Invalid response format from ERP API',
                    'status_code': response.status_code,
                    'data': {'raw_response': response.text}
                }
                
        except Exception as e:
            logger.error(f"Error calling ERP API {url}: {str(e)}")
            return {
                'success': False, 
                'message': f'Error calling ERP API: {str(e)}',
                'data': {}
            }
