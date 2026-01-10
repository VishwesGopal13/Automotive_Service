from database import db
from datetime import datetime


class Customer(db.Model):
    """
    Customer model - contains customer info and their vehicle details.
    Vehicle info is embedded in customer record (from CSV data).
    """
    __tablename__ = 'customers'

    id = db.Column(db.String(50), primary_key=True)  # cid format: C00001
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    location_human = db.Column(db.String(100))  # e.g., "Vancouver, North America"
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    # Vehicle info (embedded in customer record)
    vehicle_brand = db.Column(db.String(50))
    vehicle_model = db.Column(db.String(50))
    fuel_type = db.Column(db.String(20))  # Petrol, Diesel, Electric, Hybrid
    car_number = db.Column(db.String(20))
    vin = db.Column(db.String(50))
    warranty_years_remaining = db.Column(db.Integer, default=0)

    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job_cards = db.relationship('JobCard', backref='customer', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'address': self.address,
            'location_human': self.location_human,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'vehicle_brand': self.vehicle_brand,
            'vehicle_model': self.vehicle_model,
            'fuel_type': self.fuel_type,
            'car_number': self.car_number,
            'vin': self.vin,
            'warranty_years_remaining': self.warranty_years_remaining,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def get_vehicle_info(self):
        """Get vehicle info as a dict"""
        return {
            'brand': self.vehicle_brand,
            'model': self.vehicle_model,
            'fuel_type': self.fuel_type,
            'car_number': self.car_number,
            'vin': self.vin,
            'warranty_years_remaining': self.warranty_years_remaining
        }