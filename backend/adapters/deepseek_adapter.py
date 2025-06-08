from backend.config import settings
from backend.services.http_client import client # Assuming shared client
from loguru import logger
import httpx

API_URL = "https://api.deepseek.com/chat/completions"

async def execute(prompt: str, model: str = "deepseek-chat") -> dict:
    """Calls the DeepSeek API and returns the output and metrics."""
    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False # Use non-streaming for now
    }

    try:
        response = await client.post(API_URL, json=payload, headers=headers)
        response.raise_for_status() # Raise exception for 4xx/5xx errors
        data = response.json()

        output_text = data['choices'][0]['message']['content']
        usage = data['usage']

        # Return data in a standardized format
        return {
            "output": output_text,
            "error": None,
            "metadata": {
                "tokens_prompt": usage.get('prompt_tokens'),
                "tokens_completion": usage.get('completion_tokens'),
                "tokens": usage.get('total_tokens'),
                "model_name": data.get('model')
            }
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"DeepSeek API error: {e.response.text}")
        return {"output": None, "error": f"API Error: {e.response.status_code}", "metadata": {}}
    except Exception as e:
        logger.error(f"An unexpected error occurred with DeepSeek: {e}")
        return {"output": None, "error": str(e), "metadata": {}}