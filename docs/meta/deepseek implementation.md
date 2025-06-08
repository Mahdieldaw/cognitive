# Implementation Plan: DeepSeek Model Adapter

## Overview

This plan outlines the steps required to integrate the DeepSeek API as a new model provider within the Hybrid Engine. This process validates the model-agnostic architecture established in Phase 0 and expands the multi-model capabilities outlined in Phase 1.

### **Task: Add DeepSeek as a new Model Adapter**

Phase: 1 (Core Execution Loop)

Goal: Enable workflows to call the DeepSeek API for text generation tasks, making it available as a selectable "action" within a workflow step.

|   |   |   |
|---|---|---|
|**Component**|**File(s) to Create/Modify**|**Implementation Details & Key Code**|
|**1. Configuration**|`.env`, `config.py`|**`.env`**: Add the DeepSeek API key to the environment variables.`DEEPSEEK_API_KEY="your_api_key_here"`**`config.py`**: Make the new API key accessible through the global settings object. This avoids hardcoding secrets.`python<br/># config.py<br/>class Settings:<br/> # ... existing settings ...<br/> DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")<br/>`|
|**2. HTTP Client Setup**|`services/http_client.py` (or similar)|It's best practice to use a shared HTTP client session for making API calls. If one doesn't exist, create a new file for it. This allows for reusing connections and setting common headers.`python<br/># services/http_client.py<br/>import httpx<br/><br/># Use an async client for FastAPI<br/>client = httpx.AsyncClient(timeout=60.0) <br/>`|
|**3. Create New Adapter**|`backend/adapters/deepseek_adapter.py` (New File)|Create the new adapter file. It will contain the logic for formatting requests to the DeepSeek API, handling responses, and extracting relevant data and metrics.`python<br/># backend/adapters/deepseek_adapter.py<br/>from config import settings<br/>from services.http_client import client # Assuming shared client<br/>from loguru import logger<br/><br/>API_URL = "https://api.deepseek.com/chat/completions"<br/><br/>async def execute(prompt: str, model: str = "deepseek-chat") -> dict:<br/> """Calls the DeepSeek API and returns the output and metrics."""<br/> headers = {<br/> "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",<br/> "Content-Type": "application/json",<br/> }<br/> payload = {<br/> "model": model,<br/> "messages": [<br/> {"role": "user", "content": prompt}<br/> ],<br/> "stream": False # Use non-streaming for now<br/> }<br/><br/> try:<br/> response = await client.post(API_URL, json=payload, headers=headers)<br/> response.raise_for_status() # Raise exception for 4xx/5xx errors<br/> data = response.json()<br/><br/> output_text = data['choices'][0]['message']['content']<br/> usage = data['usage']<br/><br/> # Return data in a standardized format<br/> return {<br/> "output": output_text,<br/> "error": None,<br/> "metadata": {<br/> "tokens_prompt": usage.get('prompt_tokens'),<br/> "tokens_completion": usage.get('completion_tokens'),<br/> "tokens": usage.get('total_tokens'),<br/> "model_name": data.get('model')<br/> }<br/> }<br/> except httpx.HTTPStatusError as e:<br/> logger.error(f"DeepSeek API error: {e.response.text}")<br/> return {"output": None, "error": f"API Error: {e.response.status_code}", "metadata": {}}<br/> except Exception as e:<br/> logger.error(f"An unexpected error occurred with DeepSeek: {e}")<br/> return {"output": None, "error": str(e), "metadata": {}}<br/>`|
|**4. Integrate into Worker**|`worker.py`|Modify the worker's execution logic to recognize and delegate to the new DeepSeek adapter when a step's `action` specifies it.`python<br/># worker.py<br/># Import the new adapter at the top<br/>from adapters import deepseek_adapter<br/><br/># Modify the node execution simulation function<br/>async def execute_node(node_id: str, action: str, params: dict) -> tuple[dict, str]:<br/> """Execute a node by routing to the correct adapter based on the action."""<br/> logger.info(f"Executing node {node_id} with action '{action}'")<br/> prompt = params.get("prompt", "Default prompt") # Assume prompt is passed in params<br/><br/> if action == "deepseek_chat":<br/> result = await deepseek_adapter.execute(prompt=prompt)<br/> return result.get("output"), result.get("error"), result.get("metadata")<br/> elif action == "gemini_text_model":<br/> # ... existing logic for Gemini ...<br/> pass<br/> else:<br/> # Fallback or error for unknown action<br/> error_msg = f"Unknown action: {action}"<br/> logger.error(error_msg)<br/> return None, error_msg, {}<br/><br/># Update the main worker loop to call this new function<br/># ...<br/>output, error, metadata = await execute_node(node.id, node.action, node.params)<br/>node.metadata = metadata<br/># ...<br/>`|
|**5. Test with Workflow**|`(Manual Test)`|Manually create a new workflow template or modify an existing one in your vault to test the new action. Create a `state.json` file for a test workflow with a step that uses the `deepseek_chat` action.**Example `state.json` step:**`json<br/>{<br/> "id": "step_deepseek_1",<br/> "name": "Test DeepSeek Summarization",<br/> "action": "deepseek_chat",<br/> "params": {<br/> "prompt": "Summarize the key principles of Hybrid Thinking in three bullet points."<br/> },<br/> "status": "PENDING",<br/> "dependencies": []<br/>}<br/>`|

**Success Criteria:**

- ✅ The server starts without errors after the code changes.
    
- ✅ A workflow step with `action: "deepseek_chat"` is successfully processed by the worker.
    
- ✅ The `state.json` for the completed step shows the text output from the DeepSeek API in the `outputs` field.
    
- ✅ The `metadata` field for the step is populated with token usage (`tokens`, `tokens_prompt`, etc.) returned from the DeepSeek API.
    
- ✅ API errors from DeepSeek (e.g., invalid API key) are caught gracefully and logged in the step's `error` field.