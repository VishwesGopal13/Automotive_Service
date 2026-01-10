"""
Customer Routes - Service requests and customer management
"""
from flask import Blueprint, request, jsonify
import uuid

from database import db
from automotive_service.models.customer import Customer
from automotive_service.models.job_card import JobCard
from services.assignment_service import assignment_service
from services.ai_service import ai_service

bp = Blueprint('customer', __name__, url_prefix='/api')


# =============================================================================
# SERVICE REQUEST ENDPOINTS
# =============================================================================

@bp.route('/service-request', methods=['POST'])
def create_service_request():
    """
    POST /api/service-request
    Create a new service request (job card) for a customer.
    This is the entry point for the service workflow.
    Validates that the complaint is automotive-related before accepting.
    """
    try:
        data = request.get_json()

        if not data.get('customer_id'):
            return jsonify({'error': 'customer_id is required'}), 400

        if not data.get('complaint_text'):
            return jsonify({'error': 'complaint_text is required'}), 400

        complaint_text = data['complaint_text'].strip()

        # Validate minimum length
        if len(complaint_text) < 10:
            return jsonify({
                'error': 'Please provide more details about your vehicle issue.',
                'validation_failed': True
            }), 400

        # Validate that the complaint is automotive-related using AI
        is_valid, validation_message = ai_service.validate_complaint(complaint_text)

        if not is_valid:
            return jsonify({
                'error': validation_message,
                'validation_failed': True,
                'hint': 'Please describe an issue with your vehicle, such as unusual noises, performance problems, or maintenance needs.'
            }), 400

        # Verify customer exists
        customer = Customer.query.get(data['customer_id'])
        if not customer:
            return jsonify({'error': f"Customer {data['customer_id']} not found"}), 404

        # Create job card
        job_card_id = f"JC-{uuid.uuid4().hex[:8].upper()}"
        job_card = JobCard(
            id=job_card_id,
            customer_id=data['customer_id'],
            complaint_text=complaint_text,
            status='CREATED'
        )

        db.session.add(job_card)
        db.session.commit()

        return jsonify({
            'job_card_id': job_card_id,
            'customer_id': customer.id,
            'customer_name': customer.name,
            'vehicle': customer.get_vehicle_info(),
            'complaint_text': complaint_text,
            'status': 'CREATED',
            'message': 'Service request created successfully'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/validate-complaint', methods=['POST'])
def validate_complaint():
    """
    POST /api/validate-complaint
    Pre-validate a complaint text before creating a service request.
    Useful for real-time validation in the frontend.
    """
    try:
        data = request.get_json()

        if not data.get('complaint_text'):
            return jsonify({'is_valid': False, 'message': 'Complaint text is required'}), 400

        complaint_text = data['complaint_text'].strip()

        if len(complaint_text) < 10:
            return jsonify({
                'is_valid': False,
                'message': 'Please provide more details about your vehicle issue.'
            }), 200

        is_valid, message = ai_service.validate_complaint(complaint_text)

        return jsonify({
            'is_valid': is_valid,
            'message': message
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# SERVICE CENTER ASSIGNMENT ENDPOINTS
# =============================================================================

@bp.route('/assign-service-center/<customer_id>', methods=['GET'])
def assign_service_center(customer_id):
    """
    GET /api/assign-service-center/<customer_id>
    Assign the best available service center for a customer using pre-computed top-k index.
    Uses O(1) lookup from pre-computed haversine distances.
    """
    try:
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': f'Customer {customer_id} not found'}), 404

        result = assignment_service.assign_service_center(customer_id)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/customers/<customer_id>/nearby-centers', methods=['GET'])
def get_nearby_centers(customer_id):
    """
    GET /api/customers/<customer_id>/nearby-centers
    Get the top-k nearest service centers for a customer.
    """
    try:
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': f'Customer {customer_id} not found'}), 404

        centers = assignment_service.get_top_k_centers(customer_id)

        return jsonify({
            'customer_id': customer_id,
            'customer_name': customer.name,
            'customer_location': customer.location_human,
            'nearby_centers': centers
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# CUSTOMER ENDPOINTS
# =============================================================================

@bp.route('/customers/<customer_id>', methods=['GET'])
def get_customer(customer_id):
    """
    GET /api/customers/<customer_id>
    Get customer details including vehicle info.
    """
    try:
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': f'Customer {customer_id} not found'}), 404

        return jsonify(customer.to_dict()), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/customers', methods=['GET'])
def list_customers():
    """
    GET /api/customers
    List customers with optional pagination.
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        customers = Customer.query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'customers': [c.to_dict() for c in customers.items],
            'total': customers.total,
            'page': customers.page,
            'pages': customers.pages,
            'per_page': per_page
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
