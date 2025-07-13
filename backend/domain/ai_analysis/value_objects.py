"""
AI Analysis Domain Value Objects

Immutable value objects for AI analysis domain.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass(frozen=True)
class AnalysisId:
    """Value object for analysis ID"""
    
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Analysis ID cannot be empty")


@dataclass(frozen=True)
class ModelVersion:
    """Value object for model version"""
    
    major: int
    minor: int
    patch: int
    
    def __post_init__(self):
        if any(v < 0 for v in [self.major, self.minor, self.patch]):
            raise ValueError("Version numbers must be non-negative")
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def is_compatible_with(self, other: 'ModelVersion') -> bool:
        """Check if this version is compatible with another"""
        # Compatible if major versions match
        return self.major == other.major


@dataclass(frozen=True)
class AnalysisParameters:
    """Value object for analysis parameters"""
    
    parameters: Dict[str, Any]
    
    def __post_init__(self):
        if not isinstance(self.parameters, dict):
            raise ValueError("Parameters must be a dictionary")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get parameter value"""
        return self.parameters.get(key, default)
    
    def has(self, key: str) -> bool:
        """Check if parameter exists"""
        return key in self.parameters
    
    def validate_required(self, required_keys: List[str]) -> None:
        """Validate that required parameters are present"""
        missing = [key for key in required_keys if key not in self.parameters]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")


@dataclass(frozen=True)
class AnalysisScore:
    """Value object for analysis score"""
    
    value: float
    
    def __post_init__(self):
        if not 0.0 <= self.value <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")
    
    def is_high(self) -> bool:
        """Check if score is high (>= 0.8)"""
        return self.value >= 0.8
    
    def is_medium(self) -> bool:
        """Check if score is medium (0.5 <= score < 0.8)"""
        return 0.5 <= self.value < 0.8
    
    def is_low(self) -> bool:
        """Check if score is low (< 0.5)"""
        return self.value < 0.5


@dataclass(frozen=True)
class ConfidenceLevel:
    """Value object for confidence level"""
    
    value: float
    
    def __post_init__(self):
        if not 0.0 <= self.value <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
    
    def is_reliable(self) -> bool:
        """Check if confidence is reliable (>= 0.9)"""
        return self.value >= 0.9
    
    def is_moderate(self) -> bool:
        """Check if confidence is moderate (0.7 <= confidence < 0.9)"""
        return 0.7 <= self.value < 0.9
    
    def is_low(self) -> bool:
        """Check if confidence is low (< 0.7)"""
        return self.value < 0.7


@dataclass(frozen=True)
class AnalysisContent:
    """Value object for analysis content"""
    
    content: str
    content_type: str
    
    def __post_init__(self):
        if not self.content.strip():
            raise ValueError("Content cannot be empty")
        if not self.content_type.strip():
            raise ValueError("Content type cannot be empty")
    
    def get_word_count(self) -> int:
        """Get word count of content"""
        return len(self.content.split())
    
    def get_char_count(self) -> int:
        """Get character count of content"""
        return len(self.content)
    
    def is_code(self) -> bool:
        """Check if content is code"""
        return self.content_type in ['python', 'javascript', 'typescript', 'java', 'cpp', 'c', 'go', 'rust']
    
    def is_text(self) -> bool:
        """Check if content is text"""
        return self.content_type in ['text', 'markdown', 'html', 'xml']


@dataclass(frozen=True)
class TimeRange:
    """Value object for time range"""
    
    start_time: datetime
    end_time: datetime
    
    def __post_init__(self):
        if self.start_time >= self.end_time:
            raise ValueError("Start time must be before end time")
    
    def duration_seconds(self) -> float:
        """Get duration in seconds"""
        return (self.end_time - self.start_time).total_seconds()
    
    def duration_minutes(self) -> float:
        """Get duration in minutes"""
        return self.duration_seconds() / 60.0
    
    def contains(self, timestamp: datetime) -> bool:
        """Check if timestamp is within range"""
        return self.start_time <= timestamp <= self.end_time


@dataclass(frozen=True)
class ModelCapabilities:
    """Value object for model capabilities"""
    
    supported_types: List[str]
    max_content_size: int
    supports_streaming: bool
    supports_batch: bool
    
    def __post_init__(self):
        if not self.supported_types:
            raise ValueError("Supported types cannot be empty")
        if self.max_content_size <= 0:
            raise ValueError("Max content size must be positive")
    
    def supports_type(self, analysis_type: str) -> bool:
        """Check if model supports analysis type"""
        return analysis_type in self.supported_types
    
    def can_handle_content(self, content_size: int) -> bool:
        """Check if model can handle content size"""
        return content_size <= self.max_content_size


@dataclass(frozen=True)
class AnalysisQuality:
    """Value object for analysis quality metrics"""
    
    accuracy: float
    completeness: float
    relevance: float
    
    def __post_init__(self):
        metrics = [self.accuracy, self.completeness, self.relevance]
        if not all(0.0 <= metric <= 1.0 for metric in metrics):
            raise ValueError("All quality metrics must be between 0.0 and 1.0")
    
    def overall_quality(self) -> float:
        """Calculate overall quality score"""
        return (self.accuracy + self.completeness + self.relevance) / 3.0
    
    def is_high_quality(self) -> bool:
        """Check if analysis is high quality (>= 0.8)"""
        return self.overall_quality() >= 0.8
    
    def is_acceptable_quality(self) -> bool:
        """Check if analysis is acceptable quality (>= 0.6)"""
        return self.overall_quality() >= 0.6 