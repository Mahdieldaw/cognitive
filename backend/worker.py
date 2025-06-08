import asyncio
from datetime import datetime
from services.queue_service import queue
from services.state_manager import StateManager
from models.workflow import JobStatus
from loguru import logger
from backend.config import settings
from backend.adapters import deepseek_adapter, gemini_adapter
import httpx

def calculate_duration(start_time: datetime, end_time: datetime) -> str:
    """Calculate human-readable duration string"""
    delta = end_time - start_time
    total_seconds = int(delta.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds} sec"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes} min {seconds} sec"
    else:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours} hr {minutes} min"

def calculate_workflow_progress(workflow) -> int:
    """Calculate workflow progress percentage"""
    if not workflow.steps:
        return 0
    
    completed_steps = len([s for s in workflow.steps if s.status == JobStatus.COMPLETED])
    total_steps = len(workflow.steps)
    return int((completed_steps / total_steps) * 100)

async def execute_node(node_id: str, action: str, params: dict) -> tuple[any, str | None, dict | None]:
    """Execute a node by routing to the correct adapter based on the action."""
    logger.info(f"Executing node {node_id} with action '{action}'")
    prompt = params.get("prompt", "Default prompt") # Assume prompt is passed in params

    if action == "deepseek_chat":
        if not settings.DEEPSEEK_API_KEY or settings.DEEPSEEK_API_KEY == "your_api_key_here":
            logger.error("DEEPSEEK_API_KEY is not configured. Please set it in the .env file.")
            return None, "DEEPSEEK_API_KEY not configured", {}
        try:
            result = await deepseek_adapter.execute(prompt=prompt)
            return result.get("output"), result.get("error"), result.get("metadata")
        except httpx.ConnectError as e:
            logger.error(f"Connection error during DeepSeek API call: {e}")
            return None, f"DeepSeek API connection error: {e}", {}
        except Exception as e:
            logger.error(f"Error executing DeepSeek adapter: {e}")
            return None, str(e), {}
    elif action == "gemini_chat":
        try:
            # Extract model_name and other generation parameters from node.params
            model_name = params.get("model", "gemini-1.5-flash") # Default to 1.5 flash
            # Pass all other params as kwargs to the adapter, which will pick the relevant ones
            generation_params = {k: v for k, v in params.items() if k not in ["prompt", "model"]}
            
            result = await gemini_adapter.execute(
                prompt=prompt, 
                model_name=model_name, 
                **generation_params
            )
            return result.get("output"), result.get("error"), result.get("metadata")
        except Exception as e:
            # The adapter now includes more specific error handling, 
            # but we catch any other unexpected errors here.
            logger.error(f"Error executing Gemini adapter from worker: {e}")
            return None, str(e), {"model_name": params.get("model", "gemini-1.5-flash")}
    # Add other adapters here in the future
    # elif action == "gemini_text_model":
    #     # ... logic for Gemini ...
    #     pass
    else:
        # Fallback for unknown action or simulation for other actions
        logger.warning(f"Unknown or unhandled action: {action}. Simulating execution.")
        await asyncio.sleep(2)  # Simulate work for unknown actions
        output_sim = {
            "result": "simulated_success",
            "action": action,
            "processed_at": datetime.now().isoformat(),
            "node_id": node_id,
            "message": f"Action '{action}' simulated as no specific adapter is configured."
        }
        return output_sim, None, {"simulated": True}

async def run_worker():
    """Main worker loop"""
    logger.info("Worker started")
    
    while True:
        try:
            job = queue.get_next()
            
            if job:
                workflow_id = job["workflow_id"]
                node_id = job["node_id"]
                
                logger.info(f"Processing job: {workflow_id}/{node_id}")
                
                # Load workflow state
                state_manager = StateManager(workflow_id)
                workflow = state_manager.get()
                
                # Find the node
fdx                node = next((n for n in workflow.steps if n.id == node_id), None)
 b         ,                 if not node:
                    logger.error(f"Node {node_id} not found in workflow {workflow_id}. Skipping job.")
                    continue

                # PHASE 2: Dependency validation before execution
                if node.dependencies:
                    completed_step_ids = {s.id for s in workflow.steps if s.status == JobStatus.COMPLETED}
                    if not set(node.dependencies).issubset(completed_step_ids):
                        logger.warning(f"Dependencies not met for {workflow_id}/{node_id} (current status: {node.status}). Expected completed: {node.dependencies}, Actual completed: {completed_step_ids}. Skipping job as per plan.")
                        continue

                # If node is already completed, failed, or stopped, skip (idempotency)
                if node.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.STOPPED]:
                    logger.info(f"Node {workflow_id}/{node_id} is already in a terminal state ({node.status}). Skipping.")
                    continue
                
                node.status = JobStatus.RUNNING
                node.startTime = datetime.now()
                node.logs = node.logs or []
                node.logs.append(f"Started execution at {node.startTime.isoformat()}")
                # Set workflow to RUNNING if it's not already FAILED by a previous critical failure
                if workflow.status != JobStatus.FAILED:
                    workflow.status = JobStatus.RUNNING
                state_manager.write(workflow) # Persist RUNNING state
                
                try:
                    # Execute the node
                    output, error, metadata = await execute_node(node_id, node.action, node.params or {})
                    
                    node.endTime = datetime.now()
                    node.duration = calculate_duration(node.startTime, node.endTime)
                    node.metadata = metadata
                    
                    if error:
                        node.status = JobStatus.FAILED
                        node.error = error
                        node.logs.append(f"Failed: {error}")
                        
                        node_on_failure = getattr(node, 'on_failure', 'stop_workflow')
                        logger.info(f"Node {node_id} failed with on_failure policy: {node_on_failure}")
                        if node_on_failure == 'stop_workflow':
                            workflow.status = JobStatus.FAILED
                            logger.warning(f"Workflow {workflow_id} marked as FAILED due to critical step {node_id} failure.")
                            for step_in_workflow in workflow.steps:
                                if node_id in (step_in_workflow.dependencies or []) and \
                                   step_in_workflow.status in [JobStatus.PENDING, JobStatus.WAITING_FOR_DEPENDENCY]:
                                    step_in_workflow.status = JobStatus.STOPPED
                                    step_in_workflow.logs = step_in_workflow.logs or []
                                    step_in_workflow.logs.append(f"Upstream dependency {node_id} failed with 'stop_workflow' policy.")
                                    logger.info(f"Step {step_in_workflow.id} in workflow {workflow_id} set to STOPPED due to critical failure of {node_id}.")
                    else: # No error, node completed successfully
                        node.status = JobStatus.COMPLETED
                        node.outputs = output
                        node.logs.append(f"Completed successfully at {node.endTime.isoformat()}")
                        
                        completed_step_ids = {s.id for s in workflow.steps if s.status == JobStatus.COMPLETED}
                        logger.info(f"Node {node_id} completed. Checking for dependent nodes to queue. Completed IDs: {completed_step_ids}")
                        for next_step in workflow.steps:
                            if next_step.status == JobStatus.PENDING and \
                               next_step.dependencies and \
                               set(next_step.dependencies).issubset(completed_step_ids):
                                
                                job_key = f"{workflow_id}/{next_step.id}"
                                is_in_queue = any(f"{j['workflow_id']}/{j['node_id']}" == job_key for j in queue.queue) if hasattr(queue, 'queue') else False

                                if not is_in_queue:
                                    queue.add({"workflow_id": workflow_id, "node_id": next_step.id})
                                    next_step.status = JobStatus.WAITING_FOR_DEPENDENCY
                                    next_step.logs = next_step.logs or []
                                    next_step.logs.append(f"Queued as dependencies {next_step.dependencies} met.")
                                    logger.info(f"Queued dependent step {next_step.id} for workflow {workflow_id}. Status set to WAITING_FOR_DEPENDENCY.")
                                else:
                                    logger.info(f"Dependent step {next_step.id} for workflow {workflow_id} already in queue or its status ({next_step.status}) indicates it's handled.")
                    
                    workflow.progress = calculate_workflow_progress(workflow)
                    
                    non_terminal_statuses = [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.WAITING_FOR_DEPENDENCY]
                    is_workflow_terminal = not any(s.status in non_terminal_statuses for s in workflow.steps)

                    if is_workflow_terminal:
                        if workflow.status != JobStatus.FAILED:
                            has_critical_failure = any(
                                s.status == JobStatus.FAILED and getattr(s, 'on_failure', 'stop_workflow') == 'stop_workflow' 
                                for s in workflow.steps
                            )
                            if has_critical_failure:
                                workflow.status = JobStatus.FAILED
                            else:
                                workflow.status = JobStatus.COMPLETED
                        workflow.progress = 100
                        logger.info(f"Workflow {workflow_id} reached terminal state: {workflow.status} with progress {workflow.progress}%.")
                    else:
                        if workflow.status != JobStatus.FAILED:
                             workflow.status = JobStatus.RUNNING
                        logger.info(f"Workflow {workflow_id} is ongoing. Status: {workflow.status}, Progress: {workflow.progress}%.")

                    state_manager.write(workflow)
                    logger.info(f"Job processing finished for: {workflow_id}/{node_id}. Node status: {node.status}. Workflow status: {workflow.status}")

                except Exception as e_outer:
                    logger.error(f"Critical error processing node {node_id} in workflow {workflow_id}: {e_outer}", exc_info=True)
                    if node:
                        node.status = JobStatus.FAILED
                        node.error = f"Worker processing error: {str(e_outer)}"
                        node.endTime = datetime.now()
                        if node.startTime:
                             node.duration = calculate_duration(node.startTime, node.endTime)
                        node.logs.append(f"Critical error: {str(e_outer)}")
                        
                        node_on_failure = getattr(node, 'on_failure', 'stop_workflow')
                        if node_on_failure == 'stop_workflow':
                            workflow.status = JobStatus.FAILED
                            logger.warning(f"Workflow {workflow_id} FAILED due to critical error in step {node_id} processing.")
                            for step_in_workflow in workflow.steps:
                                if node_id in (step_in_workflow.dependencies or []) and \
                                   step_in_workflow.status in [JobStatus.PENDING, JobStatus.WAITING_FOR_DEPENDENCY]:
                                    step_in_workflow.status = JobStatus.STOPPED
                                    step_in_workflow.logs = step_in_workflow.logs or []
                                    step_in_workflow.logs.append(f"Upstream dependency {node_id} had critical processing error with 'stop_workflow' policy.")
                    else:
                        workflow.status = JobStatus.FAILED
                        logger.error(f"Workflow {workflow_id} FAILED due to critical error before node context was fully established.")

                    if state_manager.exists(): 
                         state_manager.write(workflow)
            
            else:
                # No jobs available, brief pause
                await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(5)  # Longer pause on error