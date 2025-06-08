from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any
from datetime import datetime

class ExternalDataRequest(BaseModel):
    content: str
    source_url: Optional[HttpUrl] = None
    content_type: str = "text"  # text, html, json, etc.
    metadata: Optional[Dict[str, Any]] = None
    step_name: Optional[str] = None
    action_type: str = "external_data"

class ExternalDataResponse(BaseModel):
    step_id: str
    workflow_id: str
    queued_dependents: int
    status: str