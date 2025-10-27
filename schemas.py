from pydantic import BaseModel, Field
from typing import Optional, Dict

class STTResult(BaseModel):
    text: str
    language: str

class ScribeResponse(BaseModel):
    chief_complaint: str
    hpi: str
    assessment_and_plan: str
    clinical_note: str
    policy_result: Optional[Dict] = None
    fhir_response: Optional[Dict] = None