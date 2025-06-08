from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAdapter(ABC):
    """
    Base class for all model adapters.
    Provides a common interface for interacting with different AI models.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    @abstractmethod
    async def process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request with the given parameters and return a result.
        
        Args:
            params: Dictionary containing parameters for the request
            
        Returns:
            Dictionary containing:
            - output: The model's output
            - error: Error message if any (None if successful)
            - metadata: Additional information like token count, cost, etc.
        """
        pass
class BaseAdapter(ABC):
    @abstractmethod
    async def execute(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Execute model call and return standardized response."""
        pass

    def calculate_cost(self, tokens: int, model: str) -> float:
        """Calculate cost based on token count and model."""
        # Default implementation, can be overridden by specific adapters
        # This is a placeholder and should be implemented by concrete classes
        # if they have specific cost models.
        return 0.0