from database import db
from datetime import datetime
import json

class ServiceCenter(db.Model):
    __tablename__ = 'service_centers'

    id = db.Column(db.String(10), primary_key=True)  # scid format: SC0001
    name = db.Column(db.String(100), nullable=False)
    location_human = db.Column(db.String(100))  # e.g., "Los Angeles, North America"
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    technician_available = db.Column(db.Boolean, default=False)  # yes/no from CSV
    address = db.Column(db.Text)  # Optional extended address
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    operating_hours = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    technicians = db.relationship('Technician', backref='service_center', lazy=True)
    job_cards = db.relationship('JobCard', backref='service_center', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location_human': self.location_human,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'technician_available': self.technician_available,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'operating_hours': json.loads(self.operating_hours) if self.operating_hours else None
        }

class Technician(db.Model):
    __tablename__ = 'technicians'

    id = db.Column(db.Integer, primary_key=True)
    service_center_id = db.Column(db.String(10), db.ForeignKey('service_centers.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    specializations = db.Column(db.Text)  # JSON array of specializations
    availability_status = db.Column(db.String(20), default='AVAILABLE')  # AVAILABLE, BUSY, OFF_DUTY
    current_workload = db.Column(db.Integer, default=0)
    max_workload = db.Column(db.Integer, default=3)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job_cards = db.relationship('JobCard', backref='technician', lazy=True)
    
    def get_specializations(self):
        """Get specializations as a list"""
        if self.specializations:
            return json.loads(self.specializations)
        return []
    
    def is_available(self):
        """Check if technician is available for new assignments"""
        return (self.availability_status == 'AVAILABLE' and 
                self.current_workload < self.max_workload)
    
    def to_dict(self):
        return {
            'id': self.id,
            'service_center_id': self.service_center_id,
            'name': self.name,
            'employee_id': self.employee_id,
            'specializations': self.get_specializations(),
            'availability_status': self.availability_status,
            'current_workload': self.current_workload,
            'max_workload': self.max_workload,
            'is_available': self.is_available()
        }