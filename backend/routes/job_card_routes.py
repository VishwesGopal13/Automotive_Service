"""
Job Card Routes - Job card generation and management
"""
from flask import Blueprint, request, jsonify
import json

from database import db
from automotive_service.models.customer import Customer
from automotive_service.models.job_card import JobCard
from automotive_service.models.service_center import ServiceCenter, Technician
from services.ai_service import ai_service

bp = Blueprint('job_card', __name__, url_prefix='/api')


# =============================================================================
# JOB CARD GENERATION (AI)
# =============================================================================

@bp.route('/job-card/<job_card_id>/generate', methods=['POST'])
def generate_job_card(job_card_id):
    """
    POST /api/job-card/<job_card_id>/generate
    Trigger AI to analyze complaint and generate job card details.
    This populates issue, procedures, tools, and cost estimates.
    """
    try:
        job_card = JobCard.query.get(job_card_id)
        if not job_card:
            return jsonify({'error': 'Job card not found'}), 404

        if job_card.status != 'CREATED':
            return jsonify({'error': f'Job card already processed. Current status: {job_card.status}'}), 400

        # Get customer for vehicle context
        customer = Customer.query.get(job_card.customer_id)

        # Get vehicle info for AI context
        vehicle_info = customer.get_vehicle_info() if customer else {}

        # Generate job card using AI service
        ai_result = ai_service.generate_job_card(job_card.complaint_text, vehicle_info)

        # Extract values from AI result
        issue = ai_result.get('issue', 'Vehicle inspection required')
        procedures = ai_result.get('procedures', ['Inspect vehicle'])
        tools = ai_result.get('tools', ['Basic tool set'])
        labor_hours = float(ai_result.get('labor_hours', 1.0))

        # Calculate estimated cost (average of min/max or use labor rate)
        cost_min = ai_result.get('estimated_cost_min', 75)
        cost_max = ai_result.get('estimated_cost_max', 150)
        estimated_cost = (cost_min + cost_max) / 2

        # Update job card with AI-generated details
        job_card.issue = issue
        job_card.procedures = json.dumps(procedures)
        job_card.required_tools = json.dumps(tools)
        job_card.estimated_labor_hours = labor_hours
        job_card.estimated_cost = estimated_cost
        job_card.status = 'GENERATED'

        db.session.commit()

        # Build enhanced response
        response_data = job_card.to_dict()
        response_data['ai_analysis'] = {
            'severity_category': ai_result.get('severity', 'Medium'),
            'predicted_repair_type': ai_result.get('repair_type', 'General Service'),
            'recommended_actions': procedures,
            'required_tools': tools,
            'estimated_labor_time': f"{labor_hours} hours",
            'estimated_cost_range': f"${cost_min:.0f} - ${cost_max:.0f}",
            'additional_notes': ai_result.get('additional_notes', '')
        }

        return jsonify({
            'job_card_id': job_card_id,
            'status': 'GENERATED',
            'job_card': response_data,
            'message': 'Job card generated successfully by AI'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# =============================================================================
# JOB CARD ASSIGNMENT
# =============================================================================

@bp.route('/job-card/<job_card_id>/assign', methods=['POST'])
def assign_job_card(job_card_id):
    """
    POST /api/job-card/<job_card_id>/assign
    Assign a job card to a service center and technician.
    If no technician_id is provided, automatically assigns an available technician from the service center.
    """
    try:
        job_card = JobCard.query.get(job_card_id)
        if not job_card:
            return jsonify({'error': 'Job card not found'}), 404

        if job_card.status != 'GENERATED':
            return jsonify({'error': f'Job card must be GENERATED to assign. Current status: {job_card.status}'}), 400

        data = request.get_json()

        if not data.get('service_center_id'):
            return jsonify({'error': 'service_center_id is required'}), 400

        # Verify service center exists
        service_center = ServiceCenter.query.get(data['service_center_id'])
        if not service_center:
            return jsonify({'error': f"Service center {data['service_center_id']} not found"}), 404

        # Get technician - either from request or auto-assign from service center
        technician_id = data.get('technician_id')
        technician = None

        if technician_id:
            # Use specified technician
            technician = Technician.query.get(technician_id)
            if not technician:
                return jsonify({'error': f'Technician {technician_id} not found'}), 404
        else:
            # Auto-assign: find an available technician from this service center
            # Filter by availability_status and check workload
            available_technicians = Technician.query.filter_by(
                service_center_id=data['service_center_id'],
                availability_status='AVAILABLE'
            ).all()

            # Further filter by those who are actually available (workload check)
            available_technicians = [t for t in available_technicians if t.is_available()]

            if available_technicians:
                # Assign to technician with fewest current jobs
                technician = min(
                    available_technicians,
                    key=lambda t: JobCard.query.filter_by(
                        assigned_technician_id=t.id
                    ).filter(JobCard.status.in_(['ASSIGNED', 'IN_PROGRESS'])).count()
                )
                technician_id = technician.id

        # Assign job card
        job_card.assigned_service_center_id = data['service_center_id']
        job_card.assigned_technician_id = technician_id
        job_card.status = 'ASSIGNED'

        db.session.commit()

        return jsonify({
            'job_card_id': job_card_id,
            'service_center_id': service_center.id,
            'service_center_name': service_center.name,
            'technician_id': technician_id,
            'technician_name': technician.name if technician else None,
            'status': 'ASSIGNED',
            'message': 'Job card assigned successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# =============================================================================
# JOB CARD RETRIEVAL
# =============================================================================

@bp.route('/job-card/<job_card_id>', methods=['GET'])
def get_job_card(job_card_id):
    """
    GET /api/job-card/<job_card_id>
    Get job card details with related info.
    """
    try:
        job_card = JobCard.query.get(job_card_id)
        if not job_card:
            return jsonify({'error': 'Job card not found'}), 404

        result = job_card.to_dict()

        # Add customer info
        customer = Customer.query.get(job_card.customer_id)
        if customer:
            result['customer'] = customer.to_dict()

        # Add service center info
        if job_card.assigned_service_center_id:
            service_center = ServiceCenter.query.get(job_card.assigned_service_center_id)
            if service_center:
                result['service_center'] = service_center.to_dict()

        # Add technician info
        if job_card.assigned_technician_id:
            technician = Technician.query.get(job_card.assigned_technician_id)
            if technician:
                result['technician'] = technician.to_dict()

        # Add AI analysis in a structured format for frontend
        result['ai_analysis'] = {
            'severity_category': 'Medium' if job_card.estimated_labor_hours and job_card.estimated_labor_hours > 1.5 else 'Low',
            'predicted_repair_type': job_card.issue,
            'recommended_actions': job_card.get_procedures(),
            'required_tools': job_card.get_required_tools(),
            'estimated_labor_time': f"{job_card.estimated_labor_hours} hours" if job_card.estimated_labor_hours else None,
            'estimated_cost_range': f"${job_card.estimated_cost:.2f}" if job_card.estimated_cost else None,
        }

        # Add validation report if exists
        if job_card.validation_report:
            result['validation_report'] = job_card.validation_report.to_dict()
            result['validation_report']['overall_status'] = 'approved' if job_card.validation_report.confidence_score >= 0.8 else 'needs_review'

        # Add invoice if exists
        if job_card.invoice:
            result['invoice'] = job_card.invoice.to_dict()

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

