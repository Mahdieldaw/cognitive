import asyncio
from datetime import datetime
from services.queue_service import queue
from services.state_manager import StateManager
from models.workflow import JobStatus
from loguru import logger
from backend.config import settings
from backend.adapters.openai_adapter import OpenAIAdapter
from backend.adapters.deepseek_adapter import DeepSeekAdapter # Assuming this will be updated or created similarly
from backend.adapters.gemini_adapter import GeminiAdapter   # Assuming this will be updated or created similarly
import httpx

# Initialize adapters
# Ensure API keys are handled securely, e.g., via environment variables loaded into settings
adapters = {}
if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_api_key_here":
    adapters["openai_chat"] = OpenAIAdapter(settings.OPENAI_API_KEY)
else:
    logger.warning("OpenAI API key not configured. OpenAI adapter will not be available.")

if settings.DEEPSEEK_API_KEY and settings.DEEPSEEK_API_KEY != "your_api_key_here":
    # Assuming DeepSeekAdapter is updated to match BaseAdapter interface
    # adapters["deepseek_chat"] = DeepSeekAdapter(settings.DEEPSEEK_API_KEY) 
    # For now, let's keep the old way if it's not updated yet, or comment out
    pass # Placeholder for DeepSeekAdapter instantiation if it's updated
else:
    logger.warning("DeepSeek API key not configured. DeepSeek adapter will not be available.")

if settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY != "your_api_key_here":
    # Assuming GeminiAdapter is updated to match BaseAdapter interface
    # adapters["gemini_chat"] = GeminiAdapter(settings.GOOGLE_API_KEY)
    # For now, let's keep the old way if it's not updated yet, or comment out
    pass # Placeholder for GeminiAdapter instantiation if it's updated
else:
    logger.warning("Google API key not configured. Gemini adapter will not be available.")


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
    """Execute node using appropriate adapter."""
    logger.info(f"Executing node {node_id} with action '{action}'")
    
    if action in adapters:
        adapter = adapters[action]
        prompt = params.get("prompt", "") # Default to empty string if no prompt
        # Pass all other params from the node's params to the adapter's execute method
        # The adapter's execute method will pick the kwargs it needs (e.g., model, temperature)
        model_params = {k: v for k, v in params.items() if k != "prompt"}
        
        try:
            result = await adapter.execute(prompt, **model_params)
            return result.get("output"), result.get("error"), result.get("metadata")
        except Exception as e:
            logger.error(f"Error executing adapter for action {action}: {e}", exc_info=True)
            return None, f"Adapter execution failed: {str(e)}", {"action": action}
    # Fallback for existing non-adapter based actions or if adapters are not fully refactored yet
    elif action == "deepseek_chat": # Keep old logic if DeepSeekAdapter not yet refactored
        if not settings.DEEPSEEK_API_KEY or settings.DEEPSEEK_API_KEY == "your_api_key_here":
            logger.error("DEEPSEEK_API_KEY is not configured. Please set it in the .env file.")
            return None, "DEEPSEEK_API_KEY not configured", {}
        try:
            # This assumes deepseek_adapter.execute exists and has a compatible signature
            # If DeepSeekAdapter class is used, this block should be removed or refactored
            from backend.adapters import deepseek_adapter as old_deepseek_adapter # avoid name clash
            result = await old_deepseek_adapter.execute(prompt=params.get("prompt", ""))
            return result.get("output"), result.get("error"), result.get("metadata")
        except httpx.ConnectError as e:
            logger.error(f"Connection error during DeepSeek API call: {e}")
            return None, f"DeepSeek API connection error: {e}", {}
        except Exception as e:
            logger.error(f"Error executing (old) DeepSeek adapter: {e}")
            return None, str(e), {}
    elif action == "gemini_chat": # Keep old logic if GeminiAdapter not yet refactored
        try:
            from backend.adapters import gemini_adapter as old_gemini_adapter # avoid name clash
            model_name = params.get("model", "gemini-1.5-flash")
            generation_params = {k: v for k, v in params.items() if k not in ["prompt", "model"]}
            result = await old_gemini_adapter.execute(
                prompt=params.get("prompt", ""), 
                model_name=model_name, 
                **generation_params
            )
            return result.get("output"), result.get("error"), result.get("metadata")
        except Exception as e:
            logger.error(f"Error executing (old) Gemini adapter: {e}")
            return None, str(e), {"model_name": params.get("model", "gemini-1.5-flash")}
    else:
        # Fallback for unknown actions or simulation
        logger.warning(f"Unknown action: {action}, or adapter not available/configured. Simulating execution.")
        await asyncio.sleep(1) # Simulate work
        return {"simulated": True, "message": f"Action '{action}' simulated."}, None, {"action": action, "simulated": True}

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
                        
                        # Store execution metrics from metadata
                        if metadata:
                            node.execution_metrics = {
                                "tokens": metadata.get("tokens", 0),
                                "cost": metadata.get("cost", 0.0),
                                "model": metadata.get("model", "unknown"),
                                "duration_ms": metadata.get("duration_ms", 0)
                                # Add any other relevant metrics from metadata
                            }
                        
                        # Aggregate workflow metrics
                        total_tokens = sum(
                            s.execution_metrics.get("tokens", 0) 
                            for s in workflow.steps if s.execution_metrics
                        )
                        total_cost = sum(
                            s.execution_metrics.get("cost", 0.0) 
                            for s in workflow.steps if s.execution_metrics
                        )
                        
                        workflow.metrics = {
                            "total_tokens": total_tokens,
                            "total_cost": total_cost,
                            "completed_steps": len([s for s in workflow.steps if s.status == JobStatus.COMPLETED])
                            # Add other aggregated metrics as needed
                        }
                        
                        # Cost breakdown by model
                        cost_by_model = {}
                        for step_in_wf in workflow.steps:
                            if step_in_wf.execution_metrics and "model" in step_in_wf.execution_metrics:
                                model_name = step_in_wf.execution_metrics["model"]
                                cost_by_model[model_name] = cost_by_model.get(model_name, 0.0) + step_in_wf.execution_metrics.get("cost", 0.0)
                        workflow.cost_breakdown = cost_by_model

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