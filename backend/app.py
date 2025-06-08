from fastapi import FastAPI, APIRouter, HTTPException
from contextlib import asynccontextmanager
from models.workflow import Workflow, JobStatus, WorkflowStep
from datetime import datetime
from typing import List
import uuid
import asyncio
from loguru import logger
from pathlib import Path
from config import settings
from services.state_manager import StateManager
from services.queue_service import queue
from worker import run_worker

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize worker
    logger.info("Starting Hybrid Engine Backend")
    worker_task = asyncio.create_task(run_worker())
    
    try:
        yield
    finally:
        # Shutdown: Cancel worker
        logger.info("Shutting down worker")
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass

app = FastAPI(title="Hybrid Engine Backend", lifespan=lifespan)
router = APIRouter(prefix="/api")

@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

def generate_workflow_id() -> str:
    return str(uuid.uuid4())

@router.get("/workflows")
async def get_workflows() -> List[Workflow]:
    """Get all workflows"""
    workflows = []
    workflows_dir = Path(settings.WORKFLOWS_DIR)
    
    if workflows_dir.exists():
        for workflow_dir in workflows_dir.iterdir():
            if workflow_dir.is_dir():
                try:
                    state_manager = StateManager(workflow_dir.name)
                    if state_manager.exists():
                        workflow = state_manager.get()
                        workflows.append(workflow)
                except Exception as e:
                    logger.error(f"Failed to load workflow {workflow_dir.name}: {e}")
    
    return sorted(workflows, key=lambda w: w.updatedAt, reverse=True)

@router.get("/workflows/{workflow_id}")
async def get_workflow_by_id(workflow_id: str) -> Workflow:
    """Get specific workflow by ID"""
    try:
        state_manager = StateManager(workflow_id)
        if not state_manager.exists():
            raise HTTPException(status_code=404, detail=f"Workflow with ID {workflow_id} not found")
        return state_manager.get()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workflow with ID {workflow_id} not found")
    except Exception as e:
        logger.error(f"Error retrieving workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/workflows/from-template")
async def create_workflow(template_id: str, params: dict) -> Workflow:
    """Create workflow from template and queue initial nodes"""
    try:
        workflow_id = generate_workflow_id()
        
        # Create initial workflow step (simulated template)
        initial_step = WorkflowStep(
            id=f"step_{uuid.uuid4()}",
            name=f"Initial Step - {template_id}",
            action=template_id,
            status=JobStatus.PENDING,
            dependencies=[],
            logs=[]
        )
        
        # Create workflow
        workflow = Workflow(
            id=workflow_id,
            name=f"Workflow from {template_id}",
            status=JobStatus.PENDING,
            steps=[initial_step],
            createdAt=datetime.now(),
            updatedAt=datetime.now(),
            description=f"Generated from template: {template_id}",
            progress=0
        )
        
        # Persist initial state
        state_manager = StateManager(workflow_id)
        state_manager.write(workflow)
        
        # Queue nodes with no dependencies
        for step in workflow.steps:
            if not step.dependencies:
                queue.add({"workflow_id": workflow_id, "node_id": step.id})
        
        logger.info(f"Workflow created: {workflow_id}")
        return workflow
        
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")

app.include_router(router)