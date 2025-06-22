from application import db

class Depot(db.Model):
    __tablename__ = 'depots'
    
    code = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(255))
    location = db.Column(db.String(255))

    def __repr__(self):
        return f'<Depot {self.code}: {self.name}>'