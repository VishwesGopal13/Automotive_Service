import requests
import json
import os
from typing import Dict, List, Any, Tuple
import random

class AIService:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.use_mock = not self.openai_api_key or self.openai_api_key == 'your_openai_key_here'
        self.openai_base_url = 'https://api.openai.com/v1/chat/completions'
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

    def _call_openai(self, messages: List[Dict], temperature: float = 0.3, response_format: Dict = None) -> Dict:
        """Make a call to OpenAI API"""
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature
        }
        if response_format:
            payload['response_format'] = response_format

        response = requests.post(
            self.openai_base_url,
            headers={
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            },
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")

        return response.json()

    def validate_complaint(self, complaint_text: str) -> Tuple[bool, str]:
        """
        Validate if the complaint is automotive-related.
        Returns (is_valid, message)
        """
        if self.use_mock:
            return self._mock_validate_complaint(complaint_text)

        try:
            messages = [
                {
                    'role': 'system',
                    'content': '''You are an automotive service intake validator. Your job is to determine if a customer's complaint is related to automotive/vehicle service.

Valid complaints include issues about:
- Engine, transmission, brakes, tires, suspension
- Electrical systems, lights, battery, alternator
- AC/heating, fluids (oil, coolant, brake fluid)
- Body damage, paint, windshield, mirrors
- Strange noises, vibrations, smells from the vehicle
- Performance issues, starting problems, stalling
- Scheduled maintenance (oil change, tune-up, inspection)
- Any other vehicle-related concerns

Invalid complaints include:
- Weather inquiries
- General questions not related to vehicles
- Requests for non-automotive services
- Random text or gibberish
- Abusive or inappropriate content

Respond with JSON: {"is_valid": true/false, "reason": "explanation"}'''
                },
                {
                    'role': 'user',
                    'content': f'Customer complaint: "{complaint_text}"'
                }
            ]

            response = self._call_openai(messages, temperature=0.1, response_format={"type": "json_object"})
            content = response['choices'][0]['message']['content']
            result = json.loads(content)

            return result.get('is_valid', False), result.get('reason', 'Unable to validate')

        except Exception as e:
            print(f"Validation error: {e}")
            # Fallback to mock validation on error
            return self._mock_validate_complaint(complaint_text)

    def _mock_validate_complaint(self, complaint_text: str) -> Tuple[bool, str]:
        """Mock validation for development - basic keyword check"""
        complaint_lower = complaint_text.lower()

        # Check for non-automotive keywords
        non_auto_keywords = [
            'weather', 'forecast', 'rain', 'sunny', 'temperature',
            'recipe', 'cook', 'food', 'restaurant',
            'movie', 'music', 'song', 'game',
            'stock', 'crypto', 'bitcoin',
            'hello', 'hi there', 'how are you',
            'joke', 'funny', 'poem'
        ]

        for keyword in non_auto_keywords:
            if keyword in complaint_lower:
                return False, f"Your message appears to be about '{keyword}' which is not related to automotive service. Please describe a vehicle issue."

        # Check for automotive keywords
        auto_keywords = [
            'car', 'vehicle', 'engine', 'brake', 'tire', 'wheel',
            'oil', 'transmission', 'battery', 'alternator', 'starter',
            'noise', 'sound', 'vibration', 'shake', 'smell',
            'light', 'headlight', 'taillight', 'signal',
            'ac', 'air conditioning', 'heat', 'heater',
            'window', 'windshield', 'mirror', 'door',
            'steering', 'suspension', 'shock', 'strut',
            'exhaust', 'muffler', 'catalytic',
            'coolant', 'radiator', 'overheat',
            'fuel', 'gas', 'diesel', 'mpg',
            'start', 'stall', 'idle', 'acceleration',
            'clutch', 'gear', 'shift', 'drive'
        ]

        for keyword in auto_keywords:
            if keyword in complaint_lower:
                return True, "Valid automotive complaint"

        # If no automotive keywords found but also no non-auto keywords, give benefit of doubt
        if len(complaint_text.split()) >= 5:
            return True, "Complaint accepted for review"

        return False, "Please provide more details about your vehicle issue."

    def generate_job_card(self, complaint_text: str, vehicle_info: Dict) -> Dict[str, Any]:
        """Generate structured job card from customer complaint using AI"""
        if self.use_mock:
            return self._mock_job_card_generation(complaint_text, vehicle_info)

        try:
            vehicle_str = f"{vehicle_info.get('year', '')} {vehicle_info.get('make', '')} {vehicle_info.get('model', '')}"

            messages = [
                {
                    'role': 'system',
                    'content': '''You are an expert automotive service advisor. Generate a detailed job card based on the customer's complaint.

Provide a comprehensive analysis including:
1. A clear issue description summarizing the problem
2. Severity level (Low, Medium, High, Critical)
3. Predicted repair type category
4. Step-by-step recommended procedures
5. Required tools and equipment
6. Estimated labor time in hours
7. Estimated cost range

Respond in JSON format with this structure:
{
    "issue": "Clear description of the diagnosed issue",
    "severity": "Low|Medium|High|Critical",
    "repair_type": "Category of repair (e.g., Brake System, Engine, Electrical)",
    "procedures": ["Step 1", "Step 2", ...],
    "tools": ["Tool 1", "Tool 2", ...],
    "labor_hours": 2.5,
    "estimated_cost_min": 150,
    "estimated_cost_max": 300,
    "additional_notes": "Any important notes or recommendations"
}'''
                },
                {
                    'role': 'user',
                    'content': f'''Customer complaint: "{complaint_text}"
Vehicle: {vehicle_str}

Generate a detailed job card for this service request.'''
                }
            ]

            response = self._call_openai(messages, temperature=0.3, response_format={"type": "json_object"})
            content = response['choices'][0]['message']['content']
            result = json.loads(content)

            # Ensure all required fields exist
            return {
                'issue': result.get('issue', 'Vehicle inspection required'),
                'severity': result.get('severity', 'Medium'),
                'repair_type': result.get('repair_type', 'General Service'),
                'procedures': result.get('procedures', ['Inspect vehicle', 'Diagnose issue']),
                'tools': result.get('tools', ['Basic tool set', 'Diagnostic scanner']),
                'labor_hours': float(result.get('labor_hours', 1.0)),
                'estimated_cost_min': float(result.get('estimated_cost_min', 75)),
                'estimated_cost_max': float(result.get('estimated_cost_max', 150)),
                'additional_notes': result.get('additional_notes', '')
            }

        except Exception as e:
            print(f"AI job card generation error: {e}")
            return self._mock_job_card_generation(complaint_text, vehicle_info)

    def _mock_job_card_generation(self, complaint_text: str, vehicle_info: Dict) -> Dict[str, Any]:
        """Mock job card generation for development"""
        complaint_lower = complaint_text.lower()

        if 'brake' in complaint_lower or 'grinding' in complaint_lower or 'squeak' in complaint_lower:
            return {
                'issue': 'Brake system inspection and potential pad/rotor replacement required',
                'severity': 'High',
                'repair_type': 'Brake System',
                'procedures': [
                    'Perform visual inspection of brake components',
                    'Measure brake pad thickness',
                    'Check brake rotor condition and runout',
                    'Inspect brake lines and hoses for leaks',
                    'Test brake fluid condition',
                    'Replace worn brake pads if necessary',
                    'Resurface or replace rotors if needed',
                    'Bleed brake system if fluid is contaminated',
                    'Perform test drive to verify repair'
                ],
                'tools': ['Brake pad gauge', 'Micrometer', 'Jack and jack stands', 'Lug wrench', 'Brake caliper tool', 'Brake bleeder kit', 'Torque wrench'],
                'labor_hours': 2.0,
                'estimated_cost_min': 150,
                'estimated_cost_max': 400,
                'additional_notes': 'Brake issues should be addressed immediately for safety.'
            }
        elif 'oil' in complaint_lower or 'leak' in complaint_lower:
            return {
                'issue': 'Oil system inspection - potential leak or maintenance required',
                'severity': 'Medium',
                'repair_type': 'Engine - Lubrication System',
                'procedures': [
                    'Inspect engine for oil leaks',
                    'Check oil level and condition',
                    'Drain old engine oil',
                    'Replace oil filter',
                    'Add new oil per manufacturer specifications',
                    'Check for leaks after service',
                    'Reset oil life monitor if applicable'
                ],
                'tools': ['Oil drain pan', 'Oil filter wrench', 'Socket set', 'Funnel', 'Torque wrench', 'UV dye kit (if needed)'],
                'labor_hours': 1.0,
                'estimated_cost_min': 50,
                'estimated_cost_max': 150,
                'additional_notes': 'Regular oil changes are essential for engine longevity.'
            }
        elif 'noise' in complaint_lower or 'sound' in complaint_lower or 'rattle' in complaint_lower:
            return {
                'issue': 'Diagnostic inspection for abnormal noise/sound',
                'severity': 'Medium',
                'repair_type': 'Diagnostic',
                'procedures': [
                    'Customer interview to understand noise characteristics',
                    'Road test to replicate the noise',
                    'Visual inspection of suspension components',
                    'Check exhaust system mounting',
                    'Inspect engine mounts',
                    'Use stethoscope to isolate noise source',
                    'Perform OBD scan for related codes',
                    'Document findings and recommend repairs'
                ],
                'tools': ['Automotive stethoscope', 'OBD-II scanner', 'Inspection light', 'Jack and stands', 'Pry bar'],
                'labor_hours': 1.5,
                'estimated_cost_min': 100,
                'estimated_cost_max': 200,
                'additional_notes': 'Additional repairs may be needed after diagnosis.'
            }
        elif 'start' in complaint_lower or 'battery' in complaint_lower or 'dead' in complaint_lower:
            return {
                'issue': 'Starting/electrical system diagnosis',
                'severity': 'High',
                'repair_type': 'Electrical System',
                'procedures': [
                    'Test battery voltage and capacity',
                    'Load test the battery',
                    'Check alternator output',
                    'Inspect starter motor operation',
                    'Check battery terminals and cables',
                    'Test parasitic draw if applicable',
                    'Replace faulty components',
                    'Verify proper charging system operation'
                ],
                'tools': ['Multimeter', 'Battery tester', 'Alternator tester', 'Jump pack', 'Terminal cleaner', 'Socket set'],
                'labor_hours': 1.5,
                'estimated_cost_min': 75,
                'estimated_cost_max': 300,
                'additional_notes': 'Battery replacement may be required if over 3-5 years old.'
            }
        elif 'ac' in complaint_lower or 'air condition' in complaint_lower or 'cold' in complaint_lower or 'heat' in complaint_lower:
            return {
                'issue': 'HVAC system inspection and service',
                'severity': 'Low',
                'repair_type': 'HVAC System',
                'procedures': [
                    'Check cabin air filter condition',
                    'Test AC system pressures',
                    'Check for refrigerant leaks',
                    'Inspect compressor operation',
                    'Test blend door actuators',
                    'Verify heater core function',
                    'Recharge AC system if needed'
                ],
                'tools': ['AC manifold gauges', 'Refrigerant leak detector', 'Thermometer', 'UV light', 'Vacuum pump'],
                'labor_hours': 1.5,
                'estimated_cost_min': 100,
                'estimated_cost_max': 400,
                'additional_notes': 'AC refrigerant type varies by vehicle year.'
            }
        else:
            return {
                'issue': 'Comprehensive vehicle inspection and diagnosis',
                'severity': 'Medium',
                'repair_type': 'General Service',
                'procedures': [
                    'Perform multi-point vehicle inspection',
                    'Check all fluid levels and conditions',
                    'Inspect belts and hoses',
                    'Test battery and charging system',
                    'Check tire condition and pressure',
                    'Inspect brakes visually',
                    'Scan for diagnostic trouble codes',
                    'Road test vehicle',
                    'Document all findings'
                ],
                'tools': ['OBD-II scanner', 'Multimeter', 'Inspection light', 'Tire gauge', 'Fluid testers'],
                'labor_hours': 1.0,
                'estimated_cost_min': 75,
                'estimated_cost_max': 150,
                'additional_notes': 'Full inspection recommended to identify any underlying issues.'
            }
    
    def validate_images(self, before_images: List[str], after_images: List[str]) -> Dict[str, Any]:
        """Compare before and after images"""
        if self.use_mock:
            return self._mock_image_validation()
        
        # In production, this would use computer vision API
        return self._mock_image_validation()
    
    def _mock_image_validation(self) -> Dict[str, Any]:
        """Mock image validation"""
        results = ['PASS', 'FAIL', 'UNCERTAIN']
        result = random.choice(results)
        
        return {
            'result': result,
            'confidence': random.uniform(0.7, 0.95),
            'details': f'Image comparison analysis: {result.lower()}'
        }
    
    def validate_audio(self, audio_path: str) -> Dict[str, Any]:
        """Analyze vehicle audio for anomaly detection"""
        # Mock audio validation - in production would use audio ML models
        results = ['PASS', 'FAIL']
        result = random.choice(results)
        
        return {
            'result': result,
            'confidence': random.uniform(0.6, 0.9),
            'details': f'Audio analysis indicates: {result.lower()}'
        }
    
    def speech_to_text(self, audio_path: str) -> str:
        """Convert speech to text"""
        if self.use_mock:
            return "My car is making a strange noise when I brake, and the brakes feel spongy."
        
        # In production, integrate with Whisper or similar STT service
        return "Mock transcription: Customer complaint about vehicle issue."

# Singleton instance
ai_service = AIService()