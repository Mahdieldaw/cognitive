import asyncio
from datetime import datetime
from services.queue_service import queue
from services.state_manager import StateManager
from models.workflow import JobStatus
from loguru import logger
from config import settings

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

async def execute_node_simulation(node_id: str, action: str) -> tuple[dict, str]:
    """Simulate node execution with realistic timing"""
    await asyncio.sleep(5)  # Simulate work
    
    # Simulate successful execution
    output = {
        "result": "success",
        "action": action,
        "processed_at": datetime.now().isoformat(),
        "node_id": node_id
    }
    
    return output, None  # output, error

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
                node = next((n for n in workflow.steps if n.id == node_id), None)
                if not node:
                    logger.error(f"Node {node_id} not found in workflow {workflow_id}")
                    continue
                
                # Update node to RUNNING
                node.status = JobStatus.RUNNING
                node.startTime = datetime.now()
                node.logs = node.logs or []
                node.logs.append(f"Started execution at {node.startTime.isoformat()}")
                workflow.status = JobStatus.RUNNING
                state_manager.write(workflow)
                
                # Execute the node
                try:
                    output, error = await execute_node_simulation(node_id, node.action)
                    
                    # Update node with results
                    node.endTime = datetime.now()
                    node.duration = calculate_duration(node.startTime, node.endTime)
                    
                    if error:
                        node.status = JobStatus.FAILED
                        node.error = error
                        node.logs.append(f"Failed: {error}")
                        workflow.status = JobStatus.FAILED
                    else:
                        node.status = JobStatus.COMPLETED
                        node.outputs = output
                        node.logs.append(f"Completed successfully at {node.endTime.isoformat()}")
                    
                    # Update workflow progress
                    workflow.progress = calculate_workflow_progress(workflow)
                    
                    # Check if entire workflow is complete
                    if all(s.status == JobStatus.COMPLETED for s in workflow.steps):
                        workflow.status = JobStatus.COMPLETED
                        workflow.progress = 100
                    
                    # Persist final state
                    state_manager.write(workflow)
                    logger.info(f"Job completed: {workflow_id}/{node_id} -> {node.status}")
                    
                except Exception as e:
                    logger.error(f"Error executing node {node_id}: {e}")
                    node.status = JobStatus.FAILED
                    node.error = str(e)
                    node.endTime = datetime.now()
                    node.duration = calculate_duration(node.startTime, node.endTime)
                    node.logs.append(f"Error: {str(e)}")
                    workflow.status = JobStatus.FAILED
                    state_manager.write(workflow)
            
            else:
                # No jobs available, brief pause
                await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(5)  # Longer pause on error