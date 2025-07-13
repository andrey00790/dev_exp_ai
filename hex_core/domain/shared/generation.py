"""
Generation models for RFC creation and task processing
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from pydantic import BaseModel


class TaskType(Enum):
    """Types of tasks for RFC generation"""
    ARCHITECTURE_DESIGN = "architecture_design"
    API_DESIGN = "api_design"
    SYSTEM_INTEGRATION = "system_integration"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    SECURITY_REVIEW = "security_review"
    DATABASE_DESIGN = "database_design"
    FEATURE_IMPLEMENTATION = "feature_implementation"
    TECHNICAL_ANALYSIS = "technical_analysis"


@dataclass
class UserAnswer:
    """User answer to a question"""
    question_id: str
    question: str
    answer: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class GenerationSession:
    """Session for RFC generation"""
    id: str
    task_type: TaskType
    initial_request: str
    created_at: datetime
    updated_at: datetime
    answers: List[UserAnswer] = None
    status: str = "active"
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.answers is None:
            self.answers = []
        if self.context is None:
            self.context = {}


class GenerationRequest(BaseModel):
    """Request for RFC generation"""
    task_type: str
    description: str
    context: Optional[Dict[str, Any]] = None
    questions: Optional[List[Dict[str, Any]]] = None


class GenerationResponse(BaseModel):
    """Response from RFC generation"""
    session_id: str
    status: str
    content: Optional[Dict[str, str]] = None
    questions: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


__all__ = [
    "TaskType",
    "UserAnswer", 
    "GenerationSession",
    "GenerationRequest",
    "GenerationResponse"
] 