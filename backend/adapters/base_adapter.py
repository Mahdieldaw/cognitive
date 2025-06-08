from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

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