"""
Technician Routes - Job management and technician reports
"""
from flask import Blueprint, request, jsonify
import json

from database import db
from automotive_service.models.job_card import JobCard, TechnicianUpdate
from automotive_service.models.service_center import Technician

bp = Blueprint('technician', __name__, url_prefix='/api')


# =============================================================================
# TECHNICIAN JOB MANAGEMENT
# =============================================================================

@bp.route('/technician/<int:technician_id>/jobs', methods=['GET'])
def get_technician_jobs(technician_id):
    """
    GET /api/technician/<technician_id>/jobs
    Fetch assigned job cards for a technician with full details.
    """
    try:
        from automotive_service.models.customer import Customer
        from automotive_service.models.service_center import ServiceCenter

        technician = Technician.query.get(technician_id)
        if not technician:
            return jsonify({'error': 'Technician not found'}), 404

        job_cards = JobCard.query.filter_by(assigned_technician_id=technician_id).all()

        # Build enhanced job card list
        enhanced_cards = []
        for job_card in job_cards:
            card_dict = job_card.to_dict()

            # Add customer info
            customer = Customer.query.get(job_card.customer_id)
            if customer:
                card_dict['customer'] = customer.to_dict()

            # Add service center info
            if job_card.assigned_service_center_id:
                service_center = ServiceCenter.query.get(job_card.assigned_service_center_id)
                if service_center:
                    card_dict['service_center'] = service_center.to_dict()

            # Add AI analysis
            card_dict['ai_analysis'] = {
                'severity_category': 'Medium' if job_card.estimated_labor_hours and job_card.estimated_labor_hours > 1.5 else 'Low',
                'predicted_repair_type': job_card.issue,
                'recommended_actions': job_card.get_procedures(),
                'required_tools': job_card.get_required_tools(),
                'estimated_labor_time': f"{job_card.estimated_labor_hours} hours" if job_card.estimated_labor_hours else None,
                'estimated_cost_range': f"${job_card.estimated_cost:.2f}" if job_card.estimated_cost else None,
            }

            # Add validation report if exists
            if job_card.validation_report:
                card_dict['validation_report'] = job_card.validation_report.to_dict()
                card_dict['validation_report']['overall_status'] = 'approved' if job_card.validation_report.confidence_score >= 0.8 else 'needs_review'

            enhanced_cards.append(card_dict)

        return jsonify({
            'technician_id': technician_id,
            'technician_name': technician.name,
            'job_cards': enhanced_cards
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/job-card/<job_card_id>/start', methods=['POST'])
def start_job(job_card_id):
    """
    POST /api/job-card/<job_card_id>/start
    Mark job as started by technician.
    """
    try:
        job_card = JobCard.query.get(job_card_id)
        if not job_card:
            return jsonify({'error': 'Job card not found'}), 404

        if job_card.status != 'ASSIGNED':
            return jsonify({'error': f'Job card must be ASSIGNED to start. Current status: {job_card.status}'}), 400

        job_card.status = 'IN_PROGRESS'
        db.session.commit()

        return jsonify({
            'job_card_id': job_card_id,
            'status': 'IN_PROGRESS',
            'message': 'Job started successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# =============================================================================
# TECHNICIAN REPORT SUBMISSION
# =============================================================================

@bp.route('/job-card/<job_card_id>/technician-report', methods=['POST'])
def submit_technician_report(job_card_id):
    """
    POST /api/job-card/<job_card_id>/technician-report
    Submit technician's work report for a job card.
    This includes procedures performed, tools used, labor time, and notes.
    If job is in ASSIGNED status, it will auto-start the work first.
    """
    try:
        job_card = JobCard.query.get(job_card_id)
        if not job_card:
            return jsonify({'error': 'Job card not found'}), 404

        # Allow submission from ASSIGNED (auto-start) or IN_PROGRESS status
        if job_card.status == 'ASSIGNED':
            # Auto-start the job
            job_card.status = 'IN_PROGRESS'
        elif job_card.status != 'IN_PROGRESS':
            return jsonify({'error': f'Job card must be ASSIGNED or IN_PROGRESS to submit report. Current status: {job_card.status}'}), 400

        data = request.get_json()

        if not data.get('procedures_performed'):
            return jsonify({'error': 'procedures_performed is required'}), 400

        # Check if update already exists - if so, update it instead
        existing_update = TechnicianUpdate.query.filter_by(job_card_id=job_card_id).first()

        if existing_update:
            # Update existing report
            existing_update.procedures_performed = json.dumps(data.get('procedures_performed', []))
            existing_update.tools_used = json.dumps(data.get('tools_used', []))
            existing_update.labor_time = data.get('labor_time')
            existing_update.notes = data.get('notes', '')
            tech_update = existing_update
        else:
            # Create new technician update
            tech_update = TechnicianUpdate(
                job_card_id=job_card_id,
                procedures_performed=json.dumps(data.get('procedures_performed', [])),
                tools_used=json.dumps(data.get('tools_used', [])),
                labor_time=data.get('labor_time'),
                notes=data.get('notes', '')
            )
            db.session.add(tech_update)

        # Update job card status to COMPLETED
        job_card.status = 'COMPLETED'

        db.session.commit()

        return jsonify({
            'job_card_id': job_card_id,
            'technician_update_id': tech_update.id,
            'status': 'COMPLETED',
            'technician_report': tech_update.to_dict(),
            'message': 'Technician report submitted successfully'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/job-card/<job_card_id>/technician-report', methods=['GET'])
def get_technician_report(job_card_id):
    """
    GET /api/job-card/<job_card_id>/technician-report
    Get technician's work report for a job card.
    """
    try:
        job_card = JobCard.query.get(job_card_id)
        if not job_card:
            return jsonify({'error': 'Job card not found'}), 404

        tech_update = TechnicianUpdate.query.filter_by(job_card_id=job_card_id).first()
        if not tech_update:
            return jsonify({'error': 'Technician report not found for this job card'}), 404

        return jsonify(tech_update.to_dict()), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# TECHNICIAN MANAGEMENT
# =============================================================================

@bp.route('/technicians', methods=['GET'])
def list_technicians():
    """
    GET /api/technicians
    List all technicians with their current status.
    Optional filter by service_center_id.
    """
    try:
        service_center_id = request.args.get('service_center_id', type=str)

        query = Technician.query
        if service_center_id:
            query = query.filter_by(service_center_id=service_center_id)

        technicians = query.all()

        result = []
        for tech in technicians:
            result.append({
                'id': tech.id,
                'name': tech.name,
                'employee_id': tech.employee_id,
                'service_center_id': tech.service_center_id,
                'service_center_name': tech.service_center.name if tech.service_center else None,
                'specializations': tech.get_specializations(),  # Parse JSON to list
                'availability_status': tech.availability_status,
                'current_workload': tech.current_workload,
                'max_workload': tech.max_workload,
                'is_available': tech.is_available()
            })

        return jsonify({
            'technicians': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
