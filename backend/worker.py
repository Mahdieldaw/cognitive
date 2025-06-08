import asyncio
from datetime import datetime
from .services.queue_service import queue
from .services.state_manager import StateManager
from .models.workflow import JobStatus
from loguru import logger
from .config import settings
import httpx

# Import adapters with try-except to handle missing modules
try:
    from .adapters.openai_adapter import OpenAIAdapter
    has_openai = True
except ImportError:
    logger.warning("OpenAI adapter not found or could not be imported.")
    has_openai = False

try:
    from .adapters.deepseek_adapter import DeepSeekAdapter
    has_deepseek = True
except ImportError:
    logger.warning("DeepSeek adapter not found or could not be imported.")
    has_deepseek = False

try:
    from .adapters.gemini_adapter import GeminiAdapter
    has_gemini = True
except ImportError:
    logger.warning("Gemini adapter not found or could not be imported.")
    has_gemini = False

# Initialize adapters
# Ensure API keys are handled securely, e.g., via environment variables loaded into settings
adapters = {}

# Initialize OpenAI adapter if available
if has_openai:
    openai_api_key = getattr(settings, "OPENAI_API_KEY", None)
    if openai_api_key and openai_api_key != "your_api_key_here":
        try:
            adapters["openai_chat"] = OpenAIAdapter(openai_api_key)
            logger.info("OpenAI adapter initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI adapter: {e}")
    else:
        logger.warning("OpenAI API key not configured. OpenAI adapter will not be available.")

# Initialize DeepSeek adapter if available
if has_deepseek:
    deepseek_api_key = getattr(settings, "DEEPSEEK_API_KEY", None)
    if deepseek_api_key and deepseek_api_key != "your_api_key_here":
        try:
            adapters["deepseek_chat"] = DeepSeekAdapter(deepseek_api_key)
            logger.info("DeepSeek adapter initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek adapter: {e}")
    else:
        logger.warning("DeepSeek API key not configured. DeepSeek adapter will not be available.")

# Initialize Gemini adapter if available
if has_gemini:
    gemini_api_key = getattr(settings, "GEMINI_API_KEY", None)
    if gemini_api_key and gemini_api_key != "your_api_key_here":
        try:
            adapters["gemini_chat"] = GeminiAdapter(gemini_api_key)
            logger.info("Gemini adapter initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini adapter: {e}")
    else:
        logger.warning("Google Gemini API key not configured. Gemini adapter will not be available.")

# If no adapters are available, log a warning
if not adapters:
    logger.warning("No AI model adapters are available. The worker will simulate responses only.")


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

# --- Enhanced execute_node function with adapter routing ---
async def execute_node(node_id: str, action: str, params: dict) -> tuple[any, str | None, dict | None]:
    """Execute a node by routing to the correct adapter based on the action."""
    logger.info(f"Executing node {node_id} with action '{action}'")
    
    # Check if we have an adapter for this action
    if action in adapters:
        try:
            adapter = adapters[action]
            logger.info(f"Using {action} adapter for node {node_id}")
            
            # Assume all adapters have a common interface for processing
            # This will need to be adjusted based on your actual adapter implementation
            result = await adapter.process(params)
            
            # Extract output, error, and metadata from result
            # Format will depend on your adapter implementation
            output = result.get("output", {})
            error = result.get("error")
            metadata = result.get("metadata", {"cost": 0.0, "tokens": 0})
            
            return output, error, metadata
            
        except Exception as e:
            logger.error(f"Error executing node {node_id} with {action} adapter: {e}", exc_info=True)
            return {}, f"Adapter execution error: {str(e)}", {"error": True}
    
    # Fallback to simulation if no adapter is available for this action
    logger.warning(f"No adapter available for action '{action}'. Using simulation mode.")
    await asyncio.sleep(2)  # Simulate processing time
    
    # Create simulated output based on action type
    output_sim = {
        "result": f"Simulated output for {action}",
        "action": action,
        "params_received": params
    }
    
    # Add some custom fields based on action type to make simulation more realistic
    if "chat" in action:
        output_sim["message"] = "This is a simulated AI response. The actual adapter is not available."
    elif "data" in action:
        output_sim["data"] = {"sample": "This is simulated data processing output."}
    
    metadata = {
        "simulated": True,
        "cost": 0.001,
        "tokens": 100,
        "simulation_reason": "No adapter available for this action"
    }
    
    return output_sim, None, metadata

# --- This is the complete and corrected run_worker function ---

async def run_worker():
    """Main worker loop with DAG orchestration, failure policies, and metrics."""
    logger.info("Worker started with full orchestration capabilities.")
    
    while True:
        try:
            job = queue.get_next()
            
            if not job:
                await asyncio.sleep(1)
                continue # Go to the next loop iteration if no job

            workflow_id = job["workflow_id"]
            node_id = job["node_id"]
            
            logger.info(f"Processing job: {workflow_id}/{node_id}")
            
            state_manager = StateManager(workflow_id)
            if not state_manager.exists():
                logger.error(f"State file not found for workflow {workflow_id}. Skipping job.")
                continue
            
            workflow = state_manager.get()
            node = next((n for n in workflow.steps if n.id == node_id), None)

            if not node:
                logger.error(f"Node {node_id} not found in workflow {workflow_id}. Skipping job.")
                continue

            # Idempotency Check
            if node.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.STOPPED]:
                logger.warning(f"Node {workflow_id}/{node_id} is already in a terminal state ({node.status}). Skipping.")
                continue

            # Dependency Check
            if node.dependencies:
                completed_step_ids = {s.id for s in workflow.steps if s.status == JobStatus.COMPLETED}
                if not set(node.dependencies).issubset(completed_step_ids):
                    logger.warning(f"Dependencies for {node_id} not met. Re-queuing job.")
                    queue.add(job) # Add it back to the queue
                    await asyncio.sleep(2) # Wait before retrying
                    continue

            # --- Start Node Execution ---
            node.status = JobStatus.RUNNING
            node.startTime = datetime.now()
            node.logs = node.logs or []
            node.logs.append(f"Started execution at {node.startTime.isoformat()}")
            if workflow.status not in [JobStatus.RUNNING, JobStatus.FAILED]:
                workflow.status = JobStatus.RUNNING
            state_manager.write(workflow)
            
            try:
                # Execute the node
                output, error, metadata = await execute_node(node_id, node.action, node.params or {})
                
                node.endTime = datetime.now()
                node.duration = calculate_duration(node.startTime, node.endTime)
                node.metadata = metadata

                if error:
                    # --- Node Failure Logic ---
                    node.status = JobStatus.FAILED
                    node.error = error
                    node.logs.append(f"Failed: {error}")
                    
                    if node.on_failure == 'stop_workflow':
                        workflow.status = JobStatus.FAILED
                        logger.warning(f"Workflow {workflow_id} marked as FAILED due to critical step {node_id}.")
                        # Mark downstream dependencies as STOPPED
                        for step in workflow.steps:
                            if node_id in (step.dependencies or []) and step.status in [JobStatus.PENDING, JobStatus.WAITING_FOR_DEPENDENCY]:
                                step.status = JobStatus.STOPPED
                else:
                    # --- Node Success Logic ---
                    node.status = JobStatus.COMPLETED
                    node.outputs = output
                    node.logs.append(f"Completed successfully at {node.endTime.isoformat()}")
                    
                    # --- Enqueue Dependent Nodes ---
                    completed_step_ids = {s.id for s in workflow.steps if s.status == JobStatus.COMPLETED}
                    for next_step in workflow.steps:
                        if next_step.status == JobStatus.PENDING and next_step.dependencies:
                            if set(next_step.dependencies).issubset(completed_step_ids):
                                queue.add({"workflow_id": workflow_id, "node_id": next_step.id})
                                next_step.status = JobStatus.WAITING_FOR_DEPENDENCY
                
                # --- Update Workflow-level Metrics and Status ---
                workflow.progress = calculate_workflow_progress(workflow)
                
                # Aggregate metrics (Phase 3)
                if node.metadata and 'tokens' in node.metadata:
                    total_tokens = sum(s.metadata.get('tokens', 0) for s in workflow.steps if s.metadata)
                    total_cost = sum(s.metadata.get('cost', 0) for s in workflow.steps if s.metadata)
                    workflow.metrics = {'total_tokens': total_tokens, 'total_cost': total_cost}

                # Check for workflow completion
                is_workflow_terminal = not any(s.status in [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.WAITING_FOR_DEPENDENCY] for s in workflow.steps)
                if is_workflow_terminal:
                    if workflow.status != JobStatus.FAILED:
                        workflow.status = JobStatus.COMPLETED
                    workflow.progress = 100

                state_manager.write(workflow)
                logger.info(f"Job processing finished for {node_id}. Node status: {node.status}.")

            except Exception as e_inner:
                logger.error(f"Critical error during node execution for {node_id}: {e_inner}", exc_info=True)
                node.status = JobStatus.FAILED
                node.error = str(e_inner)
                workflow.status = JobStatus.FAILED
                state_manager.write(workflow)

        except Exception as e_outer:
            logger.error(f"Major worker loop error: {e_outer}", exc_info=True)
            await asyncio.sleep(5)