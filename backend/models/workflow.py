from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class JobStatus(str, Enum):
    PENDING = 'PENDING'
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    WAITING_FOR_DEPENDENCY = 'WAITING_FOR_DEPENDENCY'
    STOPPED = 'STOPPED'

class WorkflowStep(BaseModel):
    id: str
    name: str
    action: str
    status: JobStatus
    dependencies: List[str] = []
    outputs: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    startTime: Optional[datetime] = None
    endTime: Optional[datetime] = None
    # CRITICAL: Frontend contract requirements
    duration: Optional[str] = None  # "1 min 30 sec"
    logs: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_metrics: Optional[Dict[str, Any]] = None  # Detailed metrics
    on_failure: Optional[str] = 'stop_workflow' # Literal['stop_workflow', 'continue'] - Pydantic v1 doesn't easily support Literal with str, Enum
    params: Optional[Dict[str, Any]] = None

class Workflow(BaseModel):
    id: str
    name: str
    status: JobStatus
    steps: List[WorkflowStep]
    createdAt: datetime
    updatedAt: datetime
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    parentId: Optional[str] = None
    branches: Optional[List[Dict[str, str]]] = None
    metrics: Optional[Dict[str, Any]] = None  # Aggregated workflow metrics
    cost_breakdown: Optional[Dict[str, float]] = None  # Cost per model/step