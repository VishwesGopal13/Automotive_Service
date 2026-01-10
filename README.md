# AI-Assisted Automotive Service Orchestration System

An end-to-end AI-powered platform for managing automotive service operations, from customer complaint intake to invoice generation with intelligent validation.

## 🏗️ Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│     Backend     │────▶│  Streamlit App  │
│   (Next.js)     │     │    (Flask)      │     │  (AI Assistant) │
│   Port: 3000    │     │   Port: 5000    │     │   Port: 8501    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────────────┐
                        │       SQLite DB         │
                        │ (automotive_service.db) │
                        └─────────────────────────┘
```

## 📁 Project Structure

```
├── backend/                 # Flask REST API server
│   ├── app.py              # Main application entry point
│   ├── database.py         # Database configuration
│   ├── seed_data.py        # Database seeding script
│   ├── requirements.txt    # Python dependencies
│   ├── data/               # Seed data (CSV files)
│   ├── routes/             # API route handlers
│   ├── services/           # Business logic (AI, assignment)
│   ├── automotive_service/ # Data models
│   ├── uploads/            # File uploads directory
│   └── instance/           # SQLite database
├── frontend/               # Next.js web application
│   ├── app/               # Next.js app router pages
│   └── components/        # React components
├── streamlit_app/          # Streamlit AI assistant
│   ├── app.py             # Main Streamlit application
│   └── guard.py           # AI validation logic
└── .env                    # Environment variables
```

## 🔄 Workflow

1. **Customer Complaint** → Customer submits vehicle issue via frontend
2. **AI Job Card Generation** → AI analyzes complaint and generates detailed job card
3. **Smart Assignment** → System assigns nearest service center and available technician
4. **Technician Work** → Technician performs repairs, uploads evidence
5. **AI Validation** → Revenue Guard AI validates work against job card
6. **Invoice Generation** → Automated invoice with discrepancy detection

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### 1. Clone and Setup Environment

```bash
# Copy environment file
cp .env.example .env  # Edit with your API keys
```

### 2. Start Backend (Flask API)

```bash
# Create and activate virtual environment (from project root)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies and seed database
cd backend
pip install -r requirements.txt
python3 seed_data.py

# Run the server
python3 app.py
```

Backend runs at: http://localhost:5000

### 3. Start Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:3000

### 4. Start Streamlit App (Optional - AI Assistant)

```bash
# Using the same virtual environment from root
cd streamlit_app
streamlit run app.py
```

Streamlit runs at: http://localhost:8501

## 🔌 API Endpoints

### Customer & Service Requests
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/service-request` | Create new service request |
| GET | `/api/customers` | List all customers |
| GET | `/api/customers/<id>` | Get customer details |
| GET | `/api/assign-service-center/<customer_id>` | Auto-assign service center |

### Job Cards
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/job-card/<id>/generate` | AI-generate job card details |
| POST | `/api/job-card/<id>/assign` | Assign to technician |
| GET | `/api/job-card/<id>` | Get job card details |

### Technician
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/technician/<id>/jobs` | Get assigned jobs |
| POST | `/api/technician/<id>/start-job/<job_id>` | Start working on job |
| POST | `/api/technician/<id>/complete-job/<job_id>` | Submit completed work |
| GET | `/api/technicians` | List all technicians |

### Validation & Invoicing
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/job-card/<id>/validate` | AI validation of completed work |
| POST | `/api/job-card/<id>/invoice` | Generate invoice |
| GET | `/api/job-card/<id>/validation-report` | Get validation report |

## ⚙️ Environment Variables

```env
FLASK_APP=app.py
FLASK_ENV=development
DATABASE_URL=sqlite:///automotive_service.db
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_google_ai_key_here
```

## 🛠️ Tech Stack

- **Backend**: Flask, SQLAlchemy, Flask-Migrate
- **Frontend**: Next.js 16, React 19, TailwindCSS, TypeScript
- **AI/ML**: OpenAI API, Google Gemini, Image Analysis
- **Database**: SQLite (development), PostgreSQL (production)

## 📝 License

MIT License

