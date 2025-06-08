import json
from pathlib import Path
from datetime import datetime
from ..models.workflow import Workflow
from ..config import settings
from loguru import logger

class StateManager:
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.workflow_dir = Path(settings.WORKFLOWS_DIR) / workflow_id
        self.state_file = self.workflow_dir / "state.json"
        self.workflow_dir.mkdir(parents=True, exist_ok=True)
    
    def write(self, workflow: Workflow):
        """Write workflow state with automatic updatedAt timestamp"""
        workflow.updatedAt = datetime.now()
        try:
            self.state_file.write_text(workflow.model_dump_json(indent=2))
            logger.info(f"State written for workflow {self.workflow_id}")
        except Exception as e:
            logger.error(f"Failed to write state for {self.workflow_id}: {e}")
            raise
    
    def get(self) -> Workflow:
        """Read workflow state from disk"""
        if not self.state_file.exists():
            raise FileNotFoundError(f"State file not found for workflow {self.workflow_id}")
        try:
            return Workflow.model_validate_json(self.state_file.read_text())
        except Exception as e:
            logger.error(f"Failed to read state for {self.workflow_id}: {e}")
            raise
    
    def exists(self) -> bool:
        return self.state_file.exists()