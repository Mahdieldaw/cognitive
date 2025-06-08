from fastapi import FastAPI, APIRouter, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .models.workflow import Workflow, JobStatus, WorkflowStep
from datetime import datetime
from typing import List
import uuid
import asyncio
from loguru import logger
from pathlib import Path
from .config import settings
from .services.state_manager import StateManager
from .services.queue_service import queue
from .worker import run_worker
from .recovery_manager import RecoveryManager
from .models.external_data import ExternalDataRequest, ExternalDataResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize worker and recovery manager
    logger.info("Starting Hybrid Engine Backend")

    # Initialize Recovery Manager
    recovery_manager = RecoveryManager()
    await recovery_manager.check_and_recover_orphans()
    await recovery_manager.cleanup_stale_queue_items()

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

@router.post("/workflows/{workflow_id}/external-data")
async def add_external_data(workflow_id: str, request: ExternalDataRequest) -> ExternalDataResponse:
    """Add external data to workflow and trigger dependent steps."""
    try:
        # Load target workflow
        state_manager = StateManager(workflow_id)
        if not state_manager.exists():
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
        
        workflow = state_manager.get()
        
        # Create new step for external data
        step_id = f"ext_{uuid.uuid4().hex[:8]}"
        current_time = datetime.now()
        
        external_step = WorkflowStep(
            id=step_id,
            name=request.step_name or f"External Data from {request.source_url or 'Browser'}",
            action=request.action_type,
            status=JobStatus.COMPLETED,  # Immediately completed
            dependencies=[],  # External data has no dependencies
            outputs={
                "content": request.content,
                "source_url": str(request.source_url) if request.source_url else None,
                "content_type": request.content_type,
                "captured_at": current_time.isoformat()
            },
            startTime=current_time,
            endTime=current_time,
            duration="0 sec",
            logs=[f"External data ingested at {current_time.isoformat()}"],
            metadata=request.metadata or {},
            params={"source": "browser_extension"}
        )
        
        # Add step to workflow
        workflow.steps.append(external_step)
        workflow.updatedAt = current_time
        
        # Find and queue dependent steps
        completed_step_ids = {s.id for s in workflow.steps if s.status == JobStatus.COMPLETED}
        queued_dependents = 0
        
        for step in workflow.steps:
            if (step.status == JobStatus.PENDING and 
                step.dependencies and 
                set(step.dependencies).issubset(completed_step_ids)):
                
                # Check if already queued
                job_key = f"{workflow_id}/{step.id}"
                is_queued = any(
                    f"{j['workflow_id']}/{j['node_id']}" == job_key 
                    for j in queue.queue if hasattr(queue, 'queue')
                )
                
                if not is_queued:
                    queue.add({"workflow_id": workflow_id, "node_id": step.id})
                    step.status = JobStatus.WAITING_FOR_DEPENDENCY
                    step.logs = step.logs or []
                    step.logs.append(f"Queued due to external data dependency satisfaction at {current_time.isoformat()}")
                    queued_dependents += 1
        
        # Update workflow progress
        completed_count = len([s for s in workflow.steps if s.status == JobStatus.COMPLETED])
        workflow.progress = int((completed_count / len(workflow.steps)) * 100) if workflow.steps else 0
        
        # Set workflow status to RUNNING if it was PENDING and now has queued items
        if workflow.status == JobStatus.PENDING and queued_dependents > 0:
            workflow.status = JobStatus.RUNNING
        
        # Save updated workflow
        state_manager.write(workflow)
        
        logger.info(f"External data added to workflow {workflow_id}: step {step_id}, {queued_dependents} dependents queued")
        
        return ExternalDataResponse(
            step_id=step_id,
            workflow_id=workflow_id,
            queued_dependents=queued_dependents,
            status="success"
        )
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error adding external data to workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to add external data: {str(e)}")

@router.get("/workflows/{workflow_id}/external-data")
async def get_external_data_steps(workflow_id: str):
    """Get all external data steps for a workflow."""
    try:
        state_manager = StateManager(workflow_id)
        if not state_manager.exists():
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
        
        workflow = state_manager.get()
        external_steps = [
            step for step in workflow.steps 
            if step.action == "external_data" or step.params.get("source") == "browser_extension"
        ]
        
        return {
            "workflow_id": workflow_id,
            "external_steps": external_steps,
            "count": len(external_steps)
        }
    except Exception as e:
        logger.error(f"Error retrieving external data steps: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

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

@router.post("/workflows/from-template", status_code=201)
async def create_workflow_from_template(
    template_id: str = Body(...),
    params: dict = Body(...)
) -> Workflow:
    """Create a workflow from a template, set prompt/input in step params, and queue initial job."""
    try:
        workflow_id = generate_workflow_id()
        current_time = datetime.now()
        # For demo: Simulate a template with a single LLM step. In production, load template from DB or file.
        # The key is to set the prompt/input in params or metadata for the step.
        initial_step = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name=f"LLM Step from {template_id}",
            action="gemini_chat",  # Or use template-defined action
            status=JobStatus.PENDING,
            dependencies=[],
            logs=[f"Created from template {template_id} at {current_time.isoformat()}"],
            params={"prompt": params.get("prompt", "")},
            metadata={}
        )
        workflow = Workflow(
            id=workflow_id,
            name=f"Workflow from {template_id}",
            description=f"Created from template {template_id} with params: {params}",
            status=JobStatus.PENDING,
            steps=[initial_step],
            createdAt=current_time,
            updatedAt=current_time,
            progress=0
        )
        state_manager = StateManager(workflow_id)
        state_manager.write(workflow)
        # Queue the initial step
        queue.add({"workflow_id": workflow_id, "node_id": initial_step.id})
        initial_step.status = JobStatus.WAITING_FOR_DEPENDENCY
        initial_step.logs.append(f"Queued at {datetime.now().isoformat()} as it has no dependencies.")
        state_manager.write(workflow)
        logger.info(f"Workflow {workflow_id} created from template {template_id} and initial step queued.")
        return workflow
    except Exception as e:
        logger.error(f"Failed to create workflow from template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create workflow from template: {str(e)}")

app.include_router(router)