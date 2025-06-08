import os
from pathlib import Path
from loguru import logger
from backend.services.state_manager import StateManager # Corrected import path
from backend.services.queue_service import queue         # Corrected import path
from backend.models.workflow import JobStatus            # Corrected import path
from backend.config import settings                    # Corrected import path
from datetime import datetime
import asyncio # Added for potential async operations if queue.add becomes async

class RecoveryManager:
    def __init__(self):
        self.workflows_dir = Path(settings.WORKFLOWS_DIR)
    
    async def check_and_recover_orphans(self):
        """Scan for orphaned workflows and recover them."""
        logger.info("Starting orphan workflow recovery check...")
        
        if not self.workflows_dir.exists():
            logger.info("No workflows directory found. No recovery needed.")
            return
        
        recovered_workflows = 0
        recovered_steps = 0
        
        for workflow_dir in self.workflows_dir.iterdir():
            if not workflow_dir.is_dir():
                continue
            
            workflow_id = workflow_dir.name
            try:
                state_manager = StateManager(workflow_id)
                
                if not state_manager.exists():
                    logger.warning(f"Workflow directory {workflow_id} has no state.json, skipping recovery for this entry.")
                    continue
                
                workflow = state_manager.get()
                needs_save = False
                
                # Check if workflow is orphaned (status RUNNING but no active jobs, or PENDING/WAITING with steps that should be processed)
                if workflow.status == JobStatus.RUNNING or workflow.status == JobStatus.PENDING or workflow.status == JobStatus.WAITING_FOR_DEPENDENCY:
                    logger.info(f"Found potentially orphaned or stuck workflow: {workflow_id} with status {workflow.status}")
                    
                    # Reset workflow status to PENDING for re-evaluation if it was RUNNING
                    if workflow.status == JobStatus.RUNNING:
                        workflow.status = JobStatus.PENDING
                        workflow.updatedAt = datetime.now()
                        needs_save = True
                        logger.info(f"Workflow {workflow_id} status reset to PENDING.")
                    
                    steps_to_requeue = []
                    completed_step_ids = {s.id for s in workflow.steps if s.status == JobStatus.COMPLETED}
                    
                    for step in workflow.steps:
                        # Recover RUNNING steps (were executing when crash occurred)
                        if step.status == JobStatus.RUNNING:
                            step.status = JobStatus.PENDING # Reset to PENDING for re-evaluation
                            step.error = None # Clear previous error if any
                            # step.startTime = None # Optionally reset startTime
                            step.endTime = None
                            step.logs = step.logs or []
                            step.logs.append(f"Recovered from orphaned RUNNING state at {datetime.now().isoformat()}")
                            logger.info(f"Reset orphaned RUNNING step: {step.id} to PENDING")
                            needs_save = True
                        
                        # Recover WAITING_FOR_DEPENDENCY steps that might have been missed
                        elif step.status == JobStatus.WAITING_FOR_DEPENDENCY:
                            # Check if it's genuinely waiting or if it should be PENDING for re-queue check
                            # This state implies it was queued. We'll re-evaluate its dependencies.
                            step.status = JobStatus.PENDING 
                            step.logs = step.logs or []
                            step.logs.append(f"Re-evaluating WAITING_FOR_DEPENDENCY step {step.id} during recovery at {datetime.now().isoformat()}")
                            logger.info(f"Reset WAITING_FOR_DEPENDENCY step: {step.id} to PENDING for re-evaluation")
                            needs_save = True
                        
                        # Re-queue steps that are now PENDING and have dependencies met
                        if step.status == JobStatus.PENDING:
                            if not step.dependencies or set(step.dependencies).issubset(completed_step_ids):
                                # Check if already in queue to avoid duplicates if queue is persistent
                                job_key = f"{workflow_id}/{step.id}"
                                is_in_queue = False
                                if hasattr(queue, 'queue') and isinstance(queue.queue, list): # Basic check for in-memory list queue
                                    is_in_queue = any(f"{j.get('workflow_id')}/{j.get('node_id')}" == job_key for j in queue.queue)
                                
                                if not is_in_queue:
                                    steps_to_requeue.append(step.id)
                                    step.status = JobStatus.WAITING_FOR_DEPENDENCY # Mark as queued
                                    step.logs = step.logs or []
                                    step.logs.append(f"Re-queued during recovery at {datetime.now().isoformat()}")
                                    needs_save = True
                                else:
                                    logger.info(f"Step {step.id} for workflow {workflow_id} is already in the queue or considered handled.")
                    
                    if steps_to_requeue:
                        for step_id in steps_to_requeue:
                            queue.add({"workflow_id": workflow_id, "node_id": step_id})
                            recovered_steps += 1
                        logger.info(f"Workflow {workflow_id}: {len(steps_to_requeue)} steps re-queued.")
                    
                    if needs_save:
                        # Update workflow progress
                        completed_count = len([s for s in workflow.steps if s.status == JobStatus.COMPLETED])
                        total_steps = len(workflow.steps)
                        workflow.progress = int((completed_count / total_steps) * 100) if total_steps > 0 else 0
                        
                        # If any steps were re-queued and workflow was PENDING, it might become RUNNING (or stay PENDING if worker picks it up)
                        if workflow.status == JobStatus.PENDING and recovered_steps > 0:
                             # The worker will set it to RUNNING when it picks up a task.
                             # For now, ensure it's at least PENDING to be picked up.
                             pass 

                        state_manager.write(workflow)
                        recovered_workflows += 1 # Count if any modification or re-queuing happened
                        logger.info(f"Successfully processed workflow {workflow_id} for recovery.")
            
            except Exception as e:
                logger.error(f"Error recovering workflow {workflow_id}: {e}", exc_info=True)
        
        logger.info(f"Recovery check complete: {recovered_workflows} workflows affected/processed, {recovered_steps} total steps re-queued.")
    
    async def cleanup_stale_queue_items(self):
        """Remove queue items for workflows that no longer exist (if queue is persistent and needs such cleanup)."""
        # This is more relevant for persistent queues. For an in-memory queue, it's less critical
        # as items disappear with the process. If using Redis/DB queue, implement scanning logic here.
        logger.info("Queue cleanup check initiated. (Placeholder for persistent queues)")
        # Example for a list-based in-memory queue (queue.queue):
        if hasattr(queue, 'queue') and isinstance(queue.queue, list):
            valid_jobs = []
            stale_count = 0
            for job in list(queue.queue): # Iterate over a copy for safe removal
                workflow_id = job.get("workflow_id")
                if workflow_id:
                    sm = StateManager(workflow_id)
                    if sm.exists():
                        valid_jobs.append(job)
                    else:
                        logger.warning(f"Removing stale job from queue: {job} as workflow {workflow_id} no longer exists.")
                        stale_count += 1
                else:
                    logger.warning(f"Job in queue without workflow_id: {job}. Removing.")
                    stale_count +=1
            
            if stale_count > 0:
                queue.queue = valid_jobs # Replace with filtered list
                logger.info(f"Removed {stale_count} stale job(s) from the in-memory queue.")
        pass