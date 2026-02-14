from app.extensions import db
from datetime import datetime

class Bed(db.Model):
    __tablename__ = 'beds'
    id = db.Column(db.Integer, primary_key=True)
    bed_number = db.Column(db.String(20), unique=True, nullable=False)
    ward = db.Column(db.String(100), nullable=False)
    is_occupied = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'bed_number': self.bed_number,
            'ward': self.ward,
            'is_occupied': self.is_occupied
        }

class Medicine(db.Model):
    __tablename__ = 'medicines'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    price = db.Column(db.Numeric(10, 2), default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'stock_quantity': self.stock_quantity,
            'price': float(self.price)
        }

class Ambulance(db.Model):
    __tablename__ = 'ambulances'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(50), unique=True, nullable=False)
    driver_name = db.Column(db.String(100))
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_number': self.vehicle_number,
            'driver_name': self.driver_name,
            'is_available': self.is_available
        }
