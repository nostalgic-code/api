from enum import Enum
from application import db

class CustomerUserRole(Enum):
    OWNER = "owner"
    STAFF = "staff"
    VIEWER = "viewer"

class PermissionCode(db.Model):
    __tablename__ = 'permission_codes'
    
    code = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100))
    role = db.Column(db.Enum(CustomerUserRole, values_callable=lambda x: [e.value for e in x]))
    description = db.Column(db.Text)
    default_permissions = db.Column(db.JSON)

    def __repr__(self):
        return f'<PermissionCode {self.code}: {self.name}>'