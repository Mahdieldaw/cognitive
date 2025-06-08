from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

# Add CORS middleware
origins = [
    "http://localhost",
    "http://localhost:5173",  # Default Vite dev server port
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@router.post("/workflows", status_code=201)
async def create_workflow(workflow_data: Workflow) -> Workflow:
    """Create a new workflow and queue initial nodes."""
    try:
        workflow_id = workflow_data.id or generate_workflow_id()
        
        # Validate and set defaults for the new workflow
        current_time = datetime.now()
        
        # Ensure all steps have IDs and default status if not provided
        for i, step_data in enumerate(workflow_data.steps):
            if not step_data.id:
                step_data.id = f"step_{uuid.uuid4()}" # Or use a more descriptive default ID
            if not step_data.name:
                step_data.name = f"Step {i+1} - {step_data.action[:20]}"
            step_data.status = step_data.status or JobStatus.PENDING
            step_data.createdAt = step_data.createdAt or current_time
            step_data.updatedAt = step_data.updatedAt or current_time
            step_data.logs = step_data.logs or []
            # Ensure params is a dict, default to empty if None
            step_data.params = step_data.params if step_data.params is not None else {}
            # Ensure on_failure is set, default to 'stop_workflow'
            step_data.on_failure = step_data.on_failure or 'stop_workflow'

        workflow = Workflow(
            id=workflow_id,
            name=workflow_data.name or f"Workflow {workflow_id[:8]}",
            description=workflow_data.description or "User-defined workflow",
            status=JobStatus.PENDING, # Always start as PENDING
            steps=workflow_data.steps,
            createdAt=current_time,
            updatedAt=current_time,
            progress=0,
            metadata=workflow_data.metadata or {}
        )
        
        state_manager = StateManager(workflow_id)
        if state_manager.exists():
            raise HTTPException(status_code=409, detail=f"Workflow with ID {workflow_id} already exists.")
        
        state_manager.write(workflow)
        
        # Queue initial nodes (those with no dependencies or whose dependencies are met - though for new, all are PENDING)
        queued_nodes_count = 0
        for step in workflow.steps:
            if not step.dependencies:
                queue.add({"workflow_id": workflow_id, "node_id": step.id})
                step.status = JobStatus.WAITING_FOR_DEPENDENCY # Mark as queued
                step.logs.append(f"Queued at {datetime.now().isoformat()} as it has no dependencies.")
                queued_nodes_count += 1
            else:
                # For now, assume dependencies are not met at creation time for steps with dependencies
                step.status = JobStatus.PENDING
                step.logs.append(f"Pending at {datetime.now().isoformat()}, awaiting dependencies: {step.dependencies}")

        if queued_nodes_count == 0 and workflow.steps:
            logger.warning(f"Workflow {workflow_id} created, but no initial nodes could be queued. Check dependencies.")
        elif workflow.steps:
            logger.info(f"Workflow {workflow_id} created and {queued_nodes_count} initial node(s) queued.")
        else:
            logger.info(f"Workflow {workflow_id} created with no steps.")

        # Persist updated step statuses after queuing
        state_manager.write(workflow)

        return workflow
        
    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException to preserve status code and detail
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")

@router.post("/workflows/{workflow_id}/stop")
async def stop_workflow(workflow_id: str) -> Workflow:
    """Stop a running workflow."""
    try:
        state_manager = StateManager(workflow_id)
        if not state_manager.exists():
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found.")
        
        workflow = state_manager.get()
        
        if workflow.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.STOPPED]:
            logger.info(f"Workflow {workflow_id} is already in a terminal state: {workflow.status}. No action taken.")
            return workflow

        workflow.status = JobStatus.STOPPED
        workflow.updatedAt = datetime.now()
        active_statuses = [JobStatus.RUNNING, JobStatus.PENDING, JobStatus.WAITING_FOR_DEPENDENCY]
        
        for step in workflow.steps:
            if step.status in active_statuses:
                step.status = JobStatus.STOPPED
                step.logs = step.logs or []
                step.logs.append(f"Manually stopped at {datetime.now().isoformat()}.")
        
        state_manager.write(workflow)
        logger.info(f"Workflow {workflow_id} stopped.")
        return workflow
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error stopping workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error stopping workflow: {str(e)}")

@router.post("/workflows/{workflow_id}/resume")
async def resume_workflow(workflow_id: str) -> Workflow:
    """Resume a stopped or failed workflow."""
    try:
        state_manager = StateManager(workflow_id)
        if not state_manager.exists():
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found.")
        
        workflow = state_manager.get()
        
        if workflow.status not in [JobStatus.STOPPED, JobStatus.FAILED]:
            logger.info(f"Workflow {workflow_id} is not in a resumable state (current: {workflow.status}). No action taken.")
            return workflow

        workflow.status = JobStatus.PENDING # Reset workflow status to PENDING to allow re-evaluation
        workflow.updatedAt = datetime.now()
        
        nodes_to_requeue = []
        completed_step_ids = {s.id for s in workflow.steps if s.status == JobStatus.COMPLETED}

        for step in workflow.steps:
            # Reset PENDING, WAITING_FOR_DEPENDENCY, or STOPPED steps to PENDING for re-evaluation
            if step.status in [JobStatus.PENDING, JobStatus.WAITING_FOR_DEPENDENCY, JobStatus.STOPPED]:
                step.status = JobStatus.PENDING
                step.logs = step.logs or []
                step.logs.append(f"Reset to PENDING for resume at {datetime.now().isoformat()}.")
            
            # Re-queue steps that are now PENDING and have their dependencies met or no dependencies
            if step.status == JobStatus.PENDING:
                if not step.dependencies or set(step.dependencies).issubset(completed_step_ids):
                    nodes_to_requeue.append(step.id)
                    step.status = JobStatus.WAITING_FOR_DEPENDENCY # Mark as queued
                    step.logs.append(f"Re-queued at {datetime.now().isoformat()} as dependencies met or none.")

        if not nodes_to_requeue and any(s.status == JobStatus.PENDING for s in workflow.steps):
             logger.warning(f"Workflow {workflow_id} resumed, but no nodes could be immediately re-queued. Worker will pick up PENDING tasks if dependencies get met later.")
        elif nodes_to_requeue:
            for node_id_to_queue in nodes_to_requeue:
                queue.add({"workflow_id": workflow_id, "node_id": node_id_to_queue})
            logger.info(f"Workflow {workflow_id} resumed. {len(nodes_to_requeue)} node(s) re-queued: {nodes_to_requeue}")
        else:
            logger.info(f"Workflow {workflow_id} resumed. No nodes needed immediate re-queuing (e.g., all completed or still FAILED and not reset). Worker will re-evaluate.")

        state_manager.write(workflow)
        return workflow
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error resuming workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error resuming workflow: {str(e)}")

app.include_router(router)

app.include_router(router)