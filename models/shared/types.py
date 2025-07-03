"""
Common typing definitions for AI Assistant

This module provides commonly used type aliases to reduce import duplication
across the codebase and improve type safety.
"""

from typing import List, Dict, Any, Optional, Union, Tuple, Callable, Awaitable
from datetime import datetime
from pathlib import Path

# Basic type aliases
JSON = Dict[str, Any]
OptionalStr = Optional[str]
ListStr = List[str]
DictAny = Dict[str, Any]
DictStr = Dict[str, str]
ListDict = List[Dict[str, Any]]

# Optional types
OptionalInt = Optional[int]
OptionalFloat = Optional[float]
OptionalBool = Optional[bool]
OptionalDict = Optional[Dict[str, Any]]
OptionalList = Optional[List[Any]]
OptionalDateTime = Optional[datetime]

# Union types commonly used
StrOrPath = Union[str, Path]
IntOrStr = Union[int, str]
StrOrInt = Union[str, int]
NumericType = Union[int, float]

# Function types
AsyncFunc = Callable[..., Awaitable[Any]]
SyncFunc = Callable[..., Any]
ErrorHandler = Callable[[Exception], None]
AsyncErrorHandler = Callable[[Exception], Awaitable[None]]

# File and path types
FilePath = Union[str, Path]
FileContent = Union[str, bytes]
FileMetadata = Dict[str, Any]

# API and response types
APIResponse = Dict[str, Any]
APIError = Dict[str, str]
Headers = Dict[str, str]
QueryParams = Dict[str, Union[str, int, bool, List[str]]]

# Database and model types
ModelID = Union[str, int]
PrimaryKey = Union[str, int]
ForeignKey = Union[str, int]
TimestampField = datetime

# Search and pagination types
SearchQuery = str
SearchResults = List[Dict[str, Any]]
PaginationParams = Dict[str, Union[int, str]]
SortParams = Dict[str, str]

# Validation and serialization
ValidationError = Dict[str, List[str]]
SerializationData = Dict[str, Any]

# Configuration types
ConfigValue = Union[str, int, float, bool, List[str], Dict[str, Any]]
EnvironmentConfig = Dict[str, ConfigValue]
ConnectionConfig = Dict[str, Union[str, int, bool]]

# Vector and embedding types
EmbeddingVector = List[float]
SimilarityScore = float
VectorDimensions = int

# Authentication and authorization
UserID = Union[str, int]
SessionID = str
TokenString = str
PermissionLevel = str
RoleName = str

# Task and job types
TaskID = str
JobStatus = str
ProcessingResult = Dict[str, Any]
TaskMetadata = Dict[str, Any]

# Monitoring and analytics
MetricValue = Union[int, float]
MetricData = Dict[str, MetricValue]
LogLevel = str
AlertThreshold = Union[int, float]

# Source and content types
SourceMetadata = Dict[str, Any]
ContentMetadata = Dict[str, Any]
DocumentContent = str
ChunkContent = str 