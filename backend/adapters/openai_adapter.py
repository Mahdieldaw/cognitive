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

    def calculate_cost(self, tokens: int, model: str) -> float:
        # Placeholder for actual cost calculation logic
        # This should be based on OpenAI's pricing for the specific model
        # For example:
        # if model == "gpt-4":
        #     return (tokens / 1000) * 0.03  # Example pricing
        # elif model == "gpt-3.5-turbo":
        #     return (tokens / 1000) * 0.002 # Example pricing
        return 0.0 # Default to 0 if no specific pricing is implemented