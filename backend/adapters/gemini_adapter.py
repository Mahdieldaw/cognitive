from backend.config import settings
from loguru import logger
import google.generativeai as genai
import traceback

# Configure the API key once when the module is loaded
if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Failed to configure Gemini API key: {e}")
else:
    logger.warning("GEMINI_API_KEY is not configured in settings. The Gemini adapter will not function.")

async def execute(prompt: str, model_name: str = "gemini-1.5-flash", **kwargs) -> dict:
    """Calls the Gemini API using the google-generativeai library and returns the output and metrics."""
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
        logger.error("GEMINI_API_KEY is not configured. Please set it in the .env file.")
        return {"output": None, "error": "GEMINI_API_KEY not configured", "metadata": {"model_name": model_name}}

    try:
        model = genai.GenerativeModel(model_name=model_name)

        generation_config_params = {
            "temperature": kwargs.get("temperature", 0.3),
            "max_output_tokens": kwargs.get("max_output_tokens", 8192),
            "top_p": kwargs.get("top_p", 0.95),
            "top_k": kwargs.get("top_k", 64),
        }
        # Only add stop_sequences if it's provided and not empty
        if "stop_sequences" in kwargs and kwargs["stop_sequences"]:
            generation_config_params["stop_sequences"] = kwargs["stop_sequences"]
        
        generation_config = genai.types.GenerationConfig(**generation_config_params)

        safety_settings = kwargs.get("safety_settings", [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ])

        # The google-generativeai library's generate_content is synchronous by default.
        # To use it in an async function, it should be run in a separate thread 
        # or the library should provide an async version if available.
        # For now, we'll call it directly, but for a truly async FastAPI app, 
        # this might block the event loop if the call is long.
        # Consider using asyncio.to_thread for long-running synchronous calls.
        response = await genai.GenerativeModel(model_name=model_name).generate_content_async(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings
        )

        output_text = None
        error_message = None
        metadata = {"model_name": model_name}

        if response.candidates:
            # Check for finish_reason to understand if generation was stopped (e.g. by safety)
            first_candidate = response.candidates[0]
            if first_candidate.finish_reason.name == "SAFETY":
                logger.warning(f"Gemini content generation stopped due to safety reasons: {first_candidate.safety_ratings}")
                error_message = f"Content generation stopped due to safety filters: {first_candidate.safety_ratings}"
                metadata["safety_ratings"] = [rating.__str__() for rating in first_candidate.safety_ratings]
            
            if first_candidate.content and first_candidate.content.parts:
                output_text = "".join(part.text for part in first_candidate.content.parts if hasattr(part, 'text'))
            elif not error_message: # if no text and no safety error yet
                 error_message = "Gemini API response did not contain text output."
        else:
            error_message = "No candidates returned from Gemini API."
            if response.prompt_feedback:
                logger.warning(f"Gemini prompt feedback: {response.prompt_feedback}")
                error_message += f" Prompt feedback: {response.prompt_feedback}"
                metadata["prompt_feedback"] = response.prompt_feedback.__str__()
        
        # Attempt to get token counts if available (structure might vary)
        try:
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                metadata["tokens_prompt"] = response.usage_metadata.prompt_token_count
                metadata["tokens_completion"] = response.usage_metadata.candidates_token_count
                metadata["tokens"] = response.usage_metadata.total_token_count
        except Exception as e:
            logger.debug(f"Could not parse usage_metadata from Gemini response: {e}")

        if error_message and not output_text:
            return {"output": None, "error": error_message, "metadata": metadata}
        
        return {
            "output": output_text,
            "error": error_message, # Can be None if output_text is present
            "metadata": metadata
        }

    except genai.types.BlockedPromptException as e:
        logger.error(f"Gemini API Error: Prompt was blocked. {e}")
        return {"output": None, "error": f"Gemini API Error: Prompt was blocked. {e}", "metadata": {"model_name": model_name, "details": str(e)}}
    except genai.types.StopCandidateException as e:
        logger.error(f"Gemini API Error: Candidate generation stopped. {e}")
        return {"output": None, "error": f"Gemini API Error: Candidate generation stopped. {e}", "metadata": {"model_name": model_name, "details": str(e)}}
    except Exception as e:
        logger.error(f"An unexpected error occurred with Gemini: {e}\n{traceback.format_exc()}")
        return {"output": None, "error": f"Unexpected error: {str(e)}", "metadata": {"model_name": model_name, "details": traceback.format_exc()}}