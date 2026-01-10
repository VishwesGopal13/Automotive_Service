from typing import Dict, List, Any
from models.job_card import JobCard, TechnicianUpdate, ValidationReport
from services.ai_service import ai_service
from app import db
import json

class ValidationService:
    def __init__(self):
        self.ai_service = ai_service
    
    def validate_job_completion(self, job_card: JobCard, tech_update: TechnicianUpdate) -> ValidationReport:
        """
        Comprehensive validation of job completion against job card requirements
        """
        # Compare procedures
        required_procedures = set(job_card.get_procedure())
        performed_procedures = set(tech_update.get_procedures_performed())
        missing_procedures = list(required_procedures - performed_procedures)
        
        # Compare tools
        required_tools = set(job_card.get_required_tools())
        used_tools = set(tech_update.get_tools_used())
        missing_tools = list(required_tools - used_tools)
        
        # AI-based image validation
        image_validation_result = self.ai_service.validate_images(
            tech_update.get_before_images(),
            tech_update.get_after_images()
        )
        
        # AI-based audio validation (if audio provided)
        audio_validation_result = {'result': 'PASS', 'confidence': 0.0}
        if tech_update.audio_sample:
            audio_validation_result = self.ai_service.validate_audio(tech_update.audio_sample)
        
        # Calculate overall confidence and billing risk
        confidence_score = self._calculate_confidence_score(
            missing_procedures, missing_tools,
            image_validation_result, audio_validation_result
        )
        
        billing_risk = self._assess_billing_risk(
            missing_procedures, missing_tools,
            image_validation_result, audio_validation_result
        )
        
        # Create validation report
        validation_report = ValidationReport(
            job_card_id=job_card.id,
            missing_procedures=json.dumps(missing_procedures),
            missing_tools=json.dumps(missing_tools),
            image_validation=image_validation_result['result'],
            audio_validation=audio_validation_result['result'],
            billing_risk=billing_risk,
            confidence_score=confidence_score,
            validation_details=json.dumps({
                'procedure_analysis': {
                    'required': list(required_procedures),
                    'performed': list(performed_procedures),
                    'missing': missing_procedures
                },
                'tool_analysis': {
                    'required': list(required_tools),
                    'used': list(used_tools),
                    'missing': missing_tools
                },
                'image_analysis': image_validation_result,
                'audio_analysis': audio_validation_result,
                'labor_time_comparison': {
                    'estimated': job_card.estimated_labor,
                    'actual': tech_update.labor_time
                }
            })
        )
        
        db.session.add(validation_report)
        db.session.commit()
        
        return validation_report
    
    def _calculate_confidence_score(self, missing_procedures: List[str], 
                                  missing_tools: List[str],
                                  image_result: Dict, audio_result: Dict) -> float:
        """Calculate overall confidence score for the validation"""
        base_score = 1.0
        
        # Deduct for missing procedures (more critical)
        procedure_penalty = len(missing_procedures) * 0.15
        
        # Deduct for missing tools (less critical)
        tool_penalty = len(missing_tools) * 0.05
        
        # Image validation impact
        image_penalty = 0.0
        if image_result['result'] == 'FAIL':
            image_penalty = 0.3
        elif image_result['result'] == 'UNCERTAIN':
            image_penalty = 0.1
        
        # Audio validation impact
        audio_penalty = 0.0
        if audio_result['result'] == 'FAIL':
            audio_penalty = 0.2
        
        final_score = max(0.0, base_score - procedure_penalty - tool_penalty - image_penalty - audio_penalty)
        return round(final_score, 2)
    
    def _assess_billing_risk(self, missing_procedures: List[str], 
                           missing_tools: List[str],
                           image_result: Dict, audio_result: Dict) -> bool:
        """Assess if there's a billing risk based on validation results"""
        # High risk if critical procedures are missing
        if len(missing_procedures) > 2:
            return True
        
        # High risk if image validation fails
        if image_result['result'] == 'FAIL':
            return True
        
        # Medium risk if audio validation fails
        if audio_result['result'] == 'FAIL' and len(missing_procedures) > 0:
            return True
        
        return False

# Singleton instance
validation_service = ValidationService()