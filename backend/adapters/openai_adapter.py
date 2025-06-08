import openai
from .base_adapter import BaseAdapter
from datetime import datetime
from typing import Dict, Any
from backend.config import settings # Assuming settings are in backend.config

class OpenAIAdapter(BaseAdapter):
    def __init__(self, api_key: str):
        if not api_key or api_key == "your_api_key_here":
            raise ValueError("OpenAI API key is not configured or is a placeholder.")
        self.client = openai.AsyncOpenAI(api_key=api_key)
    
    async def execute(self, prompt: str, model: str = "gpt-4", **kwargs) -> Dict[str, Any]:
        try:
            start_time = datetime.now()
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            end_time = datetime.now()
            
            usage = response.usage
            # Cost calculation can be more sophisticated, e.g., based on model-specific rates
            cost = self.calculate_cost(usage.total_tokens, model)
            
            return {
                "output": response.choices[0].message.content,
                "error": None,
                "metadata": {
                    "model": model,
                    "tokens": usage.total_tokens,
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "cost": cost,
                    "duration_ms": (end_time - start_time).total_seconds() * 1000,
                    "timestamp": start_time.isoformat()
                }
            }
        except openai.APIConnectionError as e:
            # Handle connection error
            return {
                "output": None,
                "error": f"OpenAI API connection error: {str(e)}",
                "metadata": {"model": model, "error_type": type(e).__name__}
            }
        except openai.RateLimitError as e:
            # Handle rate limit error
            return {
                "output": None,
                "error": f"OpenAI API rate limit exceeded: {str(e)}",
                "metadata": {"model": model, "error_type": type(e).__name__}
            }
        except openai.APIStatusError as e:
            # Handle API error (e.g. 400, 500)
            return {
                "output": None,
                "error": f"OpenAI API returned an API Error: {e.status_code} - {e.message}",
                "metadata": {"model": model, "error_type": type(e).__name__, "status_code": e.status_code}
            }
        except Exception as e:
            return {
                "output": None,
                "error": str(e),
                "metadata": {"model": model, "error_type": type(e).__name__}
            }
import json
import asyncio
from typing import Dict, Any, Optional
import httpx
from loguru import logger
from ..config import settings

class OpenAIAdapter:
    """
    Adapter for OpenAI API.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"
    
    async def process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request to OpenAI API.
        
        Args:
            params: Dictionary containing parameters for the request
                - prompt: The prompt to send to the model
                - model: The model to use (optional, defaults to gpt-3.5-turbo)
                - max_tokens: Maximum tokens to generate (optional)
        
        Returns:
            Dictionary containing:
            - output: The model's response
            - error: Error message if any (None if successful)
            - metadata: Additional information like token count, cost, etc.
        """
        try:
            # For simulation purposes
            logger.info(f"Simulating OpenAI API call with params: {params}")
            await asyncio.sleep(1)  # Simulate API call delay
            
            # Extract parameters
            prompt = params.get("prompt", "")
            model = params.get("model", "gpt-3.5-turbo")
            
            # Simulate a response
            simulated_response = {
                "text": f"Simulated OpenAI response for: {prompt[:50]}...",
                "model": model,
                "id": "sim_response_123"
            }
            
            # Prepare metadata
            metadata = {
                "model": model,
                "tokens": len(prompt.split()) * 2,  # Simple token estimation
                "cost": 0.002,  # Simulated cost
                "simulated": True
            }
            
            return {
                "output": simulated_response,
                "error": None,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error in OpenAI adapter: {e}")
            return {
                "output": {},
                "error": str(e),
                "metadata": {"error": True}
            }
    def calculate_cost(self, tokens: int, model: str) -> float:
        # Placeholder for actual cost calculation logic
        # This should be based on OpenAI's pricing for the specific model
        # For example:
        # if model == "gpt-4":
        #     return (tokens / 1000) * 0.03  # Example pricing
        # elif model == "gpt-3.5-turbo":
        #     return (tokens / 1000) * 0.002 # Example pricing
        return 0.0 # Default to 0 if no specific pricing is implemented