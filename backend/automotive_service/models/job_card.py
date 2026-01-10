from database import db
from datetime import datetime
import json


class JobCard(db.Model):
    """
    Job Card model - represents a service request and its lifecycle.
    Status flow: CREATED -> GENERATED -> ASSIGNED -> IN_PROGRESS -> COMPLETED -> VALIDATED -> INVOICED
    """
    __tablename__ = 'job_cards'

    id = db.Column(db.String(50), primary_key=True)
    customer_id = db.Column(db.String(50), db.ForeignKey('customers.id'), nullable=False)
    assigned_service_center_id = db.Column(db.String(10), db.ForeignKey('service_centers.id'))
    assigned_technician_id = db.Column(db.Integer, db.ForeignKey('technicians.id'))

    # Customer complaint
    complaint_text = db.Column(db.Text, nullable=False)
    complaint_audio_path = db.Column(db.String(255))

    # AI-generated job details
    issue = db.Column(db.Text)
    procedures = db.Column(db.Text)  # JSON array
    required_tools = db.Column(db.Text)  # JSON array
    estimated_labor_hours = db.Column(db.Float)
    estimated_cost = db.Column(db.Float)

    # Status tracking
    # CREATED -> GENERATED -> ASSIGNED -> IN_PROGRESS -> COMPLETED -> VALIDATED -> INVOICED
    status = db.Column(db.String(20), default='CREATED')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    technician_update = db.relationship('TechnicianUpdate', backref='job_card', uselist=False)
    validation_report = db.relationship('ValidationReport', backref='job_card', uselist=False)
    invoice = db.relationship('Invoice', backref='job_card', uselist=False)

    def get_procedures(self):
        """Get procedures as a list"""
        if self.procedures:
            return json.loads(self.procedures)
        return []

    def get_required_tools(self):
        """Get required tools as a list"""
        if self.required_tools:
            return json.loads(self.required_tools)
        return []

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'assigned_service_center_id': self.assigned_service_center_id,
            'assigned_technician_id': self.assigned_technician_id,
            'complaint_text': self.complaint_text,
            'issue': self.issue,
            'procedures': self.get_procedures(),
            'required_tools': self.get_required_tools(),
            'estimated_labor_hours': self.estimated_labor_hours,
            'estimated_cost': self.estimated_cost,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class TechnicianUpdate(db.Model):
    __tablename__ = 'technician_updates'
    
    id = db.Column(db.Integer, primary_key=True)
    job_card_id = db.Column(db.String(50), db.ForeignKey('job_cards.id'), nullable=False)
    
    # Work performed
    procedures_performed = db.Column(db.Text)  # JSON array
    tools_used = db.Column(db.Text)  # JSON array
    labor_time = db.Column(db.String(100))
    
    # Evidence
    before_images = db.Column(db.Text)  # JSON array of file paths
    after_images = db.Column(db.Text)  # JSON array of file paths
    audio_sample = db.Column(db.String(255))  # Audio file path
    
    # Additional notes
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_procedures_performed(self):
        """Get procedures performed as a list"""
        if self.procedures_performed:
            return json.loads(self.procedures_performed)
        return []
    
    def get_tools_used(self):
        """Get tools used as a list"""
        if self.tools_used:
            return json.loads(self.tools_used)
        return []
    
    def get_before_images(self):
        """Get before images as a list"""
        if self.before_images:
            return json.loads(self.before_images)
        return []
    
    def get_after_images(self):
        """Get after images as a list"""
        if self.after_images:
            return json.loads(self.after_images)
        return []

    def to_dict(self):
        return {
            'id': self.id,
            'job_card_id': self.job_card_id,
            'procedures_performed': self.get_procedures_performed(),
            'tools_used': self.get_tools_used(),
            'labor_time': self.labor_time,
            'before_images': self.get_before_images(),
            'after_images': self.get_after_images(),
            'audio_sample': self.audio_sample,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ValidationReport(db.Model):
    __tablename__ = 'validation_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    job_card_id = db.Column(db.String(50), db.ForeignKey('job_cards.id'), nullable=False)
    
    # Validation results
    confidence_score = db.Column(db.Float, nullable=False)
    billing_risk = db.Column(db.Boolean, default=False)
    
    # Detailed analysis
    missing_procedures = db.Column(db.Text)  # JSON array
    missing_tools = db.Column(db.Text)  # JSON array
    image_validation = db.Column(db.Text)  # JSON object
    audio_validation = db.Column(db.Text)  # JSON object
    validation_details = db.Column(db.Text)  # JSON object with detailed analysis
    
    # Human override
    human_override = db.Column(db.Boolean, default=False)
    override_reason = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_missing_procedures(self):
        """Get missing procedures as a list"""
        if self.missing_procedures:
            return json.loads(self.missing_procedures)
        return []
    
    def get_missing_tools(self):
        """Get missing tools as a list"""
        if self.missing_tools:
            return json.loads(self.missing_tools)
        return []
    
    def get_image_validation(self):
        """Get image validation results as a dict"""
        if self.image_validation:
            return json.loads(self.image_validation)
        return {}
    
    def get_audio_validation(self):
        """Get audio validation results as a dict"""
        if self.audio_validation:
            return json.loads(self.audio_validation)
        return {}

    def to_dict(self):
        return {
            'id': self.id,
            'job_card_id': self.job_card_id,
            'confidence_score': self.confidence_score,
            'billing_risk': self.billing_risk,
            'missing_procedures': self.get_missing_procedures(),
            'missing_tools': self.get_missing_tools(),
            'image_validation': self.get_image_validation(),
            'audio_validation': self.get_audio_validation(),
            'human_override': self.human_override,
            'override_reason': self.override_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Invoice(db.Model):
    """
    Invoice model - generated after validation is complete.
    """
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    job_card_id = db.Column(db.String(50), db.ForeignKey('job_cards.id'), nullable=False, unique=True)

    # Cost breakdown
    labor_cost = db.Column(db.Float, default=0.0)
    parts_cost = db.Column(db.Float, default=0.0)
    additional_charges = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    tax_rate = db.Column(db.Float, default=0.1)  # 10% default tax
    total_amount = db.Column(db.Float, nullable=False)

    # Details
    line_items = db.Column(db.Text)  # JSON array of line items
    notes = db.Column(db.Text)

    # Payment status
    payment_status = db.Column(db.String(20), default='PENDING')  # PENDING, PAID, CANCELLED

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_line_items(self):
        """Get line items as a list"""
        if self.line_items:
            return json.loads(self.line_items)
        return []

    def to_dict(self):
        return {
            'id': self.id,
            'job_card_id': self.job_card_id,
            'labor_cost': self.labor_cost,
            'parts_cost': self.parts_cost,
            'additional_charges': self.additional_charges,
            'discount': self.discount,
            'tax_rate': self.tax_rate,
            'total_amount': self.total_amount,
            'line_items': self.get_line_items(),
            'notes': self.notes,
            'payment_status': self.payment_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }