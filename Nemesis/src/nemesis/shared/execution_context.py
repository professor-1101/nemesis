"""Centralized execution context management."""

import os
import uuid
from datetime import datetime
from typing import Optional


class ExecutionContext:
    """Singleton pattern for execution ID management."""

    _instance: Optional['ExecutionContext'] = None
    _execution_id: Optional[str] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_execution_id(cls) -> str:
        """Get current execution ID, create if not exists."""
        if cls._execution_id is None:
            # Check environment first (for persistence across processes)
            env_execution_id = os.environ.get('NEMESIS_EXECUTION_ID')
            if env_execution_id:
                cls._execution_id = env_execution_id
            else:
                cls._execution_id = cls._generate_id()
                # Set in environment for global access
                os.environ['NEMESIS_EXECUTION_ID'] = cls._execution_id
        return cls._execution_id

    @classmethod
    def set_execution_id(cls, execution_id: str) -> None:
        """Set execution ID (for testing or external control)."""
        cls._execution_id = execution_id
        os.environ['NEMESIS_EXECUTION_ID'] = execution_id

    @classmethod
    def _generate_id(cls) -> str:
        """Generate unique execution ID."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        short_id = str(uuid.uuid4())[:8]
        return f"{timestamp}_{short_id}"
