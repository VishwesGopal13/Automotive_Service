import os
from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
from database import db

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for frontend
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///automotive_service.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)

# Create upload directories
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'images', 'before'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'images', 'after'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'audio'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'audio', 'samples'), exist_ok=True)

@app.route('/')
def index():
    return {
        'message': 'AI-Assisted Automotive Service Orchestration System',
        'version': '1.0.0',
        'status': 'running'
    }

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'database': 'connected'}

# Import models after app initialization
with app.app_context():
    from automotive_service.models.customer import Customer
    from automotive_service.models.job_card import JobCard, TechnicianUpdate, ValidationReport, Invoice
    from automotive_service.models.service_center import ServiceCenter, Technician

# Import and register blueprints
from routes.customer_routes import bp as customer_bp
from routes.job_card_routes import bp as job_card_bp
from routes.technician_routes import bp as technician_bp
from routes.validation_routes import bp as validation_bp

app.register_blueprint(customer_bp)
app.register_blueprint(job_card_bp)
app.register_blueprint(technician_bp)
app.register_blueprint(validation_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
