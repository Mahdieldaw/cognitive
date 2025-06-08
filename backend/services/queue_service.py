import json
from pathlib import Path
from typing import Dict, List, Optional
from config import settings
from loguru import logger

class MemoryQueue:
    def __init__(self, queue_file: Path = None):
        self.queue_file = queue_file or Path(settings.QUEUE_STATE_FILE)
        self.queue: List[Dict] = self._load()
    
    def _load(self) -> List[Dict]:
        """Load queue from disk, return empty list if file doesn't exist"""
        if not self.queue_file.exists():
            return []
        try:
            return json.loads(self.queue_file.read_text())
        except Exception as e:
            logger.error(f"Failed to load queue: {e}")
            return []
    
    def add(self, job: Dict):
        """Add job to queue. Job format: {'workflow_id': str, 'node_id': str}"""
        self.queue.append(job)
        self._persist()
        logger.info(f"Job added to queue: {job}")
    
    def get_next(self) -> Optional[Dict]:
        """Get and remove next job from queue"""
        if not self.queue:
            return None
        job = self.queue.pop(0)
        self._persist()
        logger.info(f"Job retrieved from queue: {job}")
        return job
    
    def _persist(self):
        """Persist queue to disk"""
        try:
            self.queue_file.write_text(json.dumps(self.queue, indent=2))
        except Exception as e:
            logger.error(f"Failed to persist queue: {e}")
            raise
    
    def size(self) -> int:
        return len(self.queue)

# Global queue instance
queue = MemoryQueue()