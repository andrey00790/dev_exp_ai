"""
AI Analysis Domain Entities

Pure business entities for AI analysis domain.
No dependencies on external frameworks or infrastructure.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Set
from enum import Enum
from uuid import uuid4


class AnalysisType(Enum):
    """Types of AI analysis"""
    CODE_ANALYSIS = "code_analysis"
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    ARCHITECTURE_ANALYSIS = "architecture_analysis"
    DOCUMENTATION_ANALYSIS = "documentation_analysis"
    QUALITY_ANALYSIS = "quality_analysis"


class AnalysisStatus(Enum):
    """Status of analysis"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(Enum):
    """Analysis priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AnalysisResult:
    """Result of AI analysis"""
    
    id: str
    analysis_type: AnalysisType
    content: str
    score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")


@dataclass
class AnalysisRequest:
    """Request for AI analysis"""
    
    id: str
    analysis_type: AnalysisType
    content: str
    priority: Priority = Priority.MEDIUM
    parameters: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())
        if not self.content.strip():
            raise ValueError("Content cannot be empty")


@dataclass
class AnalysisSession:
    """AI analysis session - aggregate root"""
    
    id: str
    request: AnalysisRequest
    status: AnalysisStatus = AnalysisStatus.PENDING
    results: List[AnalysisResult] = field(default_factory=list)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())
    
    def start_analysis(self) -> None:
        """Start the analysis session"""
        if self.status != AnalysisStatus.PENDING:
            raise ValueError(f"Cannot start analysis in {self.status.value} status")
        
        self.status = AnalysisStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def add_result(self, result: AnalysisResult) -> None:
        """Add analysis result"""
        if self.status != AnalysisStatus.RUNNING:
            raise ValueError(f"Cannot add result in {self.status.value} status")
        
        self.results.append(result)
        self.updated_at = datetime.now(timezone.utc)
    
    def complete_analysis(self) -> None:
        """Complete the analysis session"""
        if self.status != AnalysisStatus.RUNNING:
            raise ValueError(f"Cannot complete analysis in {self.status.value} status")
        
        self.status = AnalysisStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def fail_analysis(self, error_message: str) -> None:
        """Fail the analysis session"""
        if self.status == AnalysisStatus.COMPLETED:
            raise ValueError("Cannot fail completed analysis")
        
        self.status = AnalysisStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def cancel_analysis(self) -> None:
        """Cancel the analysis session"""
        if self.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]:
            raise ValueError(f"Cannot cancel analysis in {self.status.value} status")
        
        self.status = AnalysisStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def get_best_result(self) -> Optional[AnalysisResult]:
        """Get the best result based on score and confidence"""
        if not self.results:
            return None
        
        return max(self.results, key=lambda r: r.score * r.confidence)
    
    def get_average_score(self) -> float:
        """Get average score of all results"""
        if not self.results:
            return 0.0
        
        return sum(r.score for r in self.results) / len(self.results)
    
    def get_duration(self) -> Optional[float]:
        """Get analysis duration in seconds"""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds()
    
    def is_completed(self) -> bool:
        """Check if analysis is completed"""
        return self.status == AnalysisStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if analysis failed"""
        return self.status == AnalysisStatus.FAILED
    
    def is_running(self) -> bool:
        """Check if analysis is running"""
        return self.status == AnalysisStatus.RUNNING


@dataclass
class AIModel:
    """AI model configuration"""
    
    id: str
    name: str
    version: str
    model_type: str
    capabilities: Set[AnalysisType] = field(default_factory=set)
    parameters: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())
        if not self.name.strip():
            raise ValueError("Model name cannot be empty")
        if not self.version.strip():
            raise ValueError("Model version cannot be empty")
    
    def can_analyze(self, analysis_type: AnalysisType) -> bool:
        """Check if model can perform specific analysis type"""
        return analysis_type in self.capabilities
    
    def activate(self) -> None:
        """Activate the model"""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Deactivate the model"""
        self.is_active = False


@dataclass
class AnalysisMetrics:
    """Metrics for analysis performance"""
    
    id: str
    analysis_type: AnalysisType
    total_analyses: int = 0
    successful_analyses: int = 0
    failed_analyses: int = 0
    average_duration: float = 0.0
    average_score: float = 0.0
    average_confidence: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())
    
    def record_analysis(self, session: AnalysisSession) -> None:
        """Record analysis session in metrics"""
        self.total_analyses += 1
        
        if session.is_completed():
            self.successful_analyses += 1
            
            # Update averages
            duration = session.get_duration()
            if duration:
                self.average_duration = (
                    (self.average_duration * (self.successful_analyses - 1) + duration) 
                    / self.successful_analyses
                )
            
            avg_score = session.get_average_score()
            if avg_score > 0:
                self.average_score = (
                    (self.average_score * (self.successful_analyses - 1) + avg_score) 
                    / self.successful_analyses
                )
            
            if session.results:
                avg_confidence = sum(r.confidence for r in session.results) / len(session.results)
                self.average_confidence = (
                    (self.average_confidence * (self.successful_analyses - 1) + avg_confidence) 
                    / self.successful_analyses
                )
        
        elif session.is_failed():
            self.failed_analyses += 1
        
        self.updated_at = datetime.now(timezone.utc)
    
    def get_success_rate(self) -> float:
        """Get success rate of analyses"""
        if self.total_analyses == 0:
            return 0.0
        
        return self.successful_analyses / self.total_analyses
    
    def get_failure_rate(self) -> float:
        """Get failure rate of analyses"""
        if self.total_analyses == 0:
            return 0.0
        
        return self.failed_analyses / self.total_analyses 