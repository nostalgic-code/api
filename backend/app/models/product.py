from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
import json

@dataclass
class Product:
    """Simplified product model for autospares marketplace"""
    product_code: str
    description: str
    category: str
    brand: str
    base_price: float
    current_price: float
    quantity_available: int
    branch_code: str
    is_available: bool
    part_numbers: List[str]  # OEM, popular numbers combined
    unit_of_measure: str
    last_updated: datetime
    
    @classmethod
    def from_api_response(cls, api_product: dict) -> 'Product':
        """Transform API response to our simplified model"""
        # Combine all part numbers for better searchability
        part_numbers = []
        if api_product.get('oem_number'):
            part_numbers.append(api_product['oem_number'])
        if api_product.get('popular_number_one'):
            part_numbers.append(api_product['popular_number_one'])
        if api_product.get('popular_number_two'):
            part_numbers.append(api_product['popular_number_two'])
        if api_product.get('popular_number_three'):
            part_numbers.append(api_product['popular_number_three'])
        
        # Get current price from retail array or use base_retail
        current_price = cls._extract_current_price(api_product)
        
        return cls(
            product_code=api_product.get('product_code', ''),
            description=api_product.get('description', ''),
            category=api_product.get('category', ''),
            brand=api_product.get('brand', ''),
            base_price=float(api_product.get('base_retail', 0)),
            current_price=current_price,
            quantity_available=int(api_product.get('qoh', 0)),
            branch_code=api_product.get('branch_code', ''),
            is_available=int(api_product.get('qoh', 0)) > 0,
            part_numbers=part_numbers,
            unit_of_measure=api_product.get('uom', ''),
            last_updated=datetime.now()
        )
    
    @staticmethod
    def _extract_current_price(api_product: dict) -> float:
        """Extract current selling price from retail array or special price"""
        # Check for special price first
        special_price = api_product.get('special_price')
        if special_price and special_price != '':
            try:
                return float(special_price)
            except (ValueError, TypeError):
                pass
        
        # Check retail array
        retail = api_product.get('retail', [])
        if retail and isinstance(retail, list) and len(retail) > 0:
            try:
                return float(retail[0])
            except (ValueError, TypeError, IndexError):
                pass
        
        # Fall back to base retail
        return float(api_product.get('base_retail', 0))