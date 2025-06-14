from application import db
from datetime import datetime
import json
from typing import List

class Product(db.Model):
    """SQLAlchemy Product model for autospares marketplace"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.Text)
    category = db.Column(db.String(100), index=True)
    brand = db.Column(db.String(100), index=True)
    base_price = db.Column(db.Numeric(10, 2), default=0.00)
    current_price = db.Column(db.Numeric(10, 2), default=0.00, index=True)
    quantity_available = db.Column(db.Integer, default=0)
    branch_code = db.Column(db.String(50), index=True)
    is_available = db.Column(db.Boolean, default=False, index=True)
    part_numbers = db.Column(db.Text)  # Store as JSON string
    unit_of_measure = db.Column(db.String(20))
    data_hash = db.Column(db.String(64), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_sync = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Product {self.product_code}>'
    
    @classmethod
    def from_api_response(cls, api_product: dict) -> 'Product':
        """Transform API response to our SQLAlchemy model"""
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
            part_numbers=json.dumps(part_numbers),
            unit_of_measure=api_product.get('uom', ''),
            last_updated=datetime.utcnow()
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
    
    def get_part_numbers_list(self) -> List[str]:
        """Get part numbers as a list"""
        if self.part_numbers:
            try:
                return json.loads(self.part_numbers)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'product_code': self.product_code,
            'description': self.description,
            'category': self.category,
            'brand': self.brand,
            'base_price': float(self.base_price) if self.base_price else 0.0,
            'current_price': float(self.current_price) if self.current_price else 0.0,
            'quantity_available': self.quantity_available,
            'branch_code': self.branch_code,
            'is_available': self.is_available,
            'part_numbers': self.get_part_numbers_list(),
            'unit_of_measure': self.unit_of_measure,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }