"""
Validation & Invoice Routes - AI validation, invoice generation, and audit reports
"""
from flask import Blueprint, request, jsonify
import json

from database import db
from automotive_service.models.customer import Customer
from automotive_service.models.job_card import JobCard, TechnicianUpdate, ValidationReport, Invoice

bp = Blueprint('validation', __name__, url_prefix='/api')


# =============================================================================
# AI VALIDATION ENDPOINTS
# =============================================================================

@bp.route('/job-card/<job_card_id>/validate', methods=['POST'])
def validate_job_card(job_card_id):
    """
    POST /api/job-card/<job_card_id>/validate
    Trigger AI validation for a completed job card.
    Compares technician report against AI-generated job card requirements.
    """
    try:
        job_card = JobCard.query.get(job_card_id)
        if not job_card:
            return jsonify({'error': 'Job card not found'}), 404

        if job_card.status != 'COMPLETED':
            return jsonify({'error': f'Job card must be COMPLETED before validation. Current status: {job_card.status}'}), 400

        # Check if validation already exists
        existing_validation = ValidationReport.query.filter_by(job_card_id=job_card_id).first()
        if existing_validation:
            return jsonify({
                'job_card_id': job_card_id,
                'validation_report_id': existing_validation.id,
                'status': 'already_validated',
                'validation_report': existing_validation.to_dict(),
                'message': 'Validation report already exists'
            }), 200

        # Get technician report
        tech_update = TechnicianUpdate.query.filter_by(job_card_id=job_card_id).first()
        if not tech_update:
            return jsonify({'error': 'No technician report found. Cannot validate.'}), 400

        # Placeholder AI validation logic
        # In production, this would call the AI service to compare procedures
        required_procedures = job_card.get_procedures()
        performed_procedures = tech_update.get_procedures_performed()
        required_tools = job_card.get_required_tools()
        used_tools = tech_update.get_tools_used()

        # Simple validation: check if all required procedures were performed
        missing_procedures = [p for p in required_procedures if p not in performed_procedures]
        missing_tools = [t for t in required_tools if t not in used_tools]

        # Calculate confidence score (placeholder logic)
        if required_procedures:
            procedure_match = 1 - (len(missing_procedures) / len(required_procedures))
        else:
            procedure_match = 1.0

        confidence_score = procedure_match
        billing_risk = len(missing_procedures) > 0

        # Create validation report
        validation_report = ValidationReport(
            job_card_id=job_card_id,
            confidence_score=confidence_score,
            billing_risk=billing_risk,
            missing_procedures=json.dumps(missing_procedures),
            missing_tools=json.dumps(missing_tools),
            image_validation=json.dumps({'status': 'pending'}),
            audio_validation=json.dumps({'status': 'pending'})
        )

        # Update job card status
        job_card.status = 'VALIDATED'

        db.session.add(validation_report)
        db.session.commit()

        return jsonify({
            'job_card_id': job_card_id,
            'validation_report_id': validation_report.id,
            'validation_report': validation_report.to_dict(),
            'status': 'VALIDATED',
            'message': 'Validation completed successfully'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/job-card/<job_card_id>/validation-report', methods=['GET'])
def get_validation_report_by_job(job_card_id):
    """
    GET /api/job-card/<job_card_id>/validation-report
    Get validation report for a job card.
    """
    try:
        job_card = JobCard.query.get(job_card_id)
        if not job_card:
            return jsonify({'error': 'Job card not found'}), 404

        report = ValidationReport.query.filter_by(job_card_id=job_card_id).first()
        if not report:
            return jsonify({'error': 'Validation report not found for this job card'}), 404

        return jsonify(report.to_dict()), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# INVOICE GENERATION ENDPOINTS
# =============================================================================

@bp.route('/job-card/<job_card_id>/generate-invoice', methods=['POST'])
def generate_invoice(job_card_id):
    """
    POST /api/job-card/<job_card_id>/generate-invoice
    Generate invoice for a validated job card.
    """
    try:
        job_card = JobCard.query.get(job_card_id)
        if not job_card:
            return jsonify({'error': 'Job card not found'}), 404

        if job_card.status != 'VALIDATED':
            return jsonify({'error': f'Job card must be VALIDATED to generate invoice. Current status: {job_card.status}'}), 400

        # Check if invoice already exists
        existing_invoice = Invoice.query.filter_by(job_card_id=job_card_id).first()
        if existing_invoice:
            return jsonify({
                'job_card_id': job_card_id,
                'invoice_id': existing_invoice.id,
                'status': 'already_generated',
                'invoice': existing_invoice.to_dict(),
                'message': 'Invoice already exists'
            }), 200

        data = request.get_json() or {}

        # Get technician report for labor calculation
        tech_update = TechnicianUpdate.query.filter_by(job_card_id=job_card_id).first()

        # Calculate costs (using provided values or defaults)
        labor_rate = data.get('labor_rate', 75.0)  # Default $75/hour
        labor_hours = float(tech_update.labor_time.replace('hours', '').strip()) if tech_update and tech_update.labor_time else job_card.estimated_labor_hours or 1.0
        labor_cost = labor_hours * labor_rate

        parts_cost = data.get('parts_cost', 0.0)
        additional_charges = data.get('additional_charges', 0.0)
        discount = data.get('discount', 0.0)
        tax_rate = data.get('tax_rate', 0.1)  # 10% default

        subtotal = labor_cost + parts_cost + additional_charges - discount
        tax = subtotal * tax_rate
        total_amount = subtotal + tax

        # Build line items
        line_items = [
            {'description': 'Labor', 'hours': labor_hours, 'rate': labor_rate, 'amount': labor_cost}
        ]
        if parts_cost > 0:
            line_items.append({'description': 'Parts', 'amount': parts_cost})
        if additional_charges > 0:
            line_items.append({'description': 'Additional Charges', 'amount': additional_charges})
        if discount > 0:
            line_items.append({'description': 'Discount', 'amount': -discount})
        line_items.append({'description': f'Tax ({tax_rate*100:.0f}%)', 'amount': tax})

        # Create invoice
        invoice = Invoice(
            job_card_id=job_card_id,
            labor_cost=labor_cost,
            parts_cost=parts_cost,
            additional_charges=additional_charges,
            discount=discount,
            tax_rate=tax_rate,
            total_amount=total_amount,
            line_items=json.dumps(line_items),
            notes=data.get('notes', '')
        )

        # Update job card status
        job_card.status = 'INVOICED'

        db.session.add(invoice)
        db.session.commit()

        return jsonify({
            'job_card_id': job_card_id,
            'invoice_id': invoice.id,
            'invoice': invoice.to_dict(),
            'status': 'INVOICED',
            'message': 'Invoice generated successfully'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/job-card/<job_card_id>/invoice', methods=['GET'])
def get_invoice(job_card_id):
    """
    GET /api/job-card/<job_card_id>/invoice
    Get invoice for a job card.
    """
    try:
        job_card = JobCard.query.get(job_card_id)
        if not job_card:
            return jsonify({'error': 'Job card not found'}), 404

        invoice = Invoice.query.filter_by(job_card_id=job_card_id).first()
        if not invoice:
            return jsonify({'error': 'Invoice not found for this job card'}), 404

        return jsonify(invoice.to_dict()), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# AUDIT & FINAL REPORT ENDPOINTS
# =============================================================================

@bp.route('/job-card/<job_card_id>/audit-report', methods=['GET'])
def get_audit_report(job_card_id):
    """
    GET /api/job-card/<job_card_id>/audit-report
    Get comprehensive audit report for a job card.
    Includes customer info, job card, technician report, validation, and invoice.
    """
    try:
        job_card = JobCard.query.get(job_card_id)
        if not job_card:
            return jsonify({'error': 'Job card not found'}), 404

        # Get customer info
        customer = Customer.query.get(job_card.customer_id)

        # Get technician report
        tech_update = TechnicianUpdate.query.filter_by(job_card_id=job_card_id).first()

        # Get validation report
        validation_report = ValidationReport.query.filter_by(job_card_id=job_card_id).first()

        # Get invoice
        invoice = Invoice.query.filter_by(job_card_id=job_card_id).first()

        audit_report = {
            'job_card_id': job_card_id,
            'status': job_card.status,
            'created_at': job_card.created_at.isoformat() if job_card.created_at else None,

            # Customer & Vehicle Info
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'location': customer.location_human,
                'vehicle': customer.get_vehicle_info()
            } if customer else None,

            # Original Complaint & AI-Generated Job Card
            'service_request': {
                'complaint_text': job_card.complaint_text,
                'ai_diagnosed_issue': job_card.issue,
                'required_procedures': job_card.get_procedures(),
                'required_tools': job_card.get_required_tools(),
                'estimated_labor_hours': job_card.estimated_labor_hours,
                'estimated_cost': job_card.estimated_cost,
                'assigned_service_center_id': job_card.assigned_service_center_id,
                'assigned_technician_id': job_card.assigned_technician_id
            },

            # Technician Report
            'technician_report': tech_update.to_dict() if tech_update else None,

            # AI Validation
            'validation_report': validation_report.to_dict() if validation_report else None,

            # Invoice
            'invoice': invoice.to_dict() if invoice else None,

            # Audit Summary
            'audit_summary': {
                'has_technician_report': tech_update is not None,
                'has_validation': validation_report is not None,
                'has_invoice': invoice is not None,
                'validation_passed': validation_report.confidence_score >= 0.8 if validation_report else None,
                'billing_risk': validation_report.billing_risk if validation_report else None,
                'total_amount': invoice.total_amount if invoice else None
            }
        }

        return jsonify(audit_report), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
