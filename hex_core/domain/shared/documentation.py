"""
Documentation Models for AI Assistant
Модели для системы генерации документации
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class CodeLanguage(Enum):
    """Поддерживаемые языки программирования"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"
    C = "c"
    CSHARP = "csharp"
    PHP = "php"
    RUBY = "ruby"
    OTHER = "other"


class DocumentationType(Enum):
    """Типы документации"""
    API_DOCS = "api_docs"
    README = "readme"
    TUTORIAL = "tutorial"
    REFERENCE = "reference"
    ARCHITECTURE = "architecture"
    DEPLOYMENT = "deployment"
    CONTRIBUTING = "contributing"
    CHANGELOG = "changelog"
    USER_GUIDE = "user_guide"
    DEVELOPER_GUIDE = "developer_guide"


@dataclass
class CodeFile:
    """Файл с кодом"""
    filename: str
    content: str
    language: CodeLanguage
    size_bytes: Optional[int] = None
    last_modified: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeRepository:
    """Репозиторий с кодом"""
    name: str
    path: str
    files: List[CodeFile]
    language: Optional[CodeLanguage] = None
    main_language: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeAnalysis:
    """Результат анализа кода"""
    functions: List[Dict[str, Any]] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=list)
    modules: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    complexity_score: float = 1.0
    architecture_patterns: List[str] = field(default_factory=list)
    security_concerns: List[str] = field(default_factory=list)
    performance_notes: List[str] = field(default_factory=list)
    test_coverage: Optional[float] = None
    code_quality_score: Optional[float] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentationSection:
    """Секция документации"""
    title: str
    content: str
    order: int = 0
    subsections: List['DocumentationSection'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedDocumentation:
    """Сгенерированная документация"""
    id: Optional[str] = None
    title: str = ""
    summary: str = ""
    sections: List[DocumentationSection] = field(default_factory=list)
    full_content: str = ""
    code_analysis: Optional[CodeAnalysis] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class DocumentationRequest:
    """Запрос на генерацию документации"""
    code_input: Union[CodeFile, CodeRepository, str]
    documentation_type: DocumentationType
    target_audience: str = "developers"
    detail_level: str = "detailed"  # brief, detailed, comprehensive
    include_examples: bool = True
    include_installation: bool = True
    include_api_reference: bool = True
    custom_sections: List[str] = field(default_factory=list)
    style_preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentationResponse:
    """Ответ с сгенерированной документацией"""
    documentation: GeneratedDocumentation
    message: str
    generation_time_seconds: float
    analysis_stats: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class CodeAnalysisRequest:
    """Запрос на анализ кода"""
    code_input: Union[CodeFile, CodeRepository, str]
    analysis_depth: str = "detailed"  # basic, detailed, comprehensive
    include_metrics: bool = True
    include_security_check: bool = True
    include_performance_analysis: bool = True
    custom_checks: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# Константы возможностей документации
DOCUMENTATION_CAPABILITIES = {
    "supported_languages": [lang.value for lang in CodeLanguage],
    "documentation_types": [doc_type.value for doc_type in DocumentationType],
    "features": [  # Добавляем ключ "features" для совместимости с тестом
        "function_extraction",
        "class_analysis", 
        "dependency_mapping",
        "complexity_calculation",
        "security_scanning",
        "performance_analysis",
        "architecture_detection",
        "test_coverage_analysis"
    ],
    "analysis_features": [
        "function_extraction",
        "class_analysis", 
        "dependency_mapping",
        "complexity_calculation",
        "security_scanning",
        "performance_analysis",
        "architecture_detection",
        "test_coverage_analysis"
    ],
    "output_formats": [
        "markdown",
        "html",
        "pdf",
        "json",
        "rst",
        "asciidoc"
    ],
    "customization_options": [
        "target_audience",
        "detail_level",
        "custom_sections",
        "style_preferences",
        "template_selection"
    ],
    "integration_capabilities": [
        "api_endpoint",
        "cli_tool",
        "ide_plugin",
        "git_hooks",
        "ci_cd_pipeline"
    ],
    "advanced_features": [
        "multi_language_support",
        "cross_reference_generation",
        "auto_example_generation",
        "version_comparison",
        "interactive_docs",
        "live_updates"
    ]
}


# Дополнительные утилиты
def get_language_from_extension(filename: str) -> CodeLanguage:
    """Определяет язык программирования по расширению файла"""
    extension_map = {
        '.py': CodeLanguage.PYTHON,
        '.js': CodeLanguage.JAVASCRIPT,
        '.ts': CodeLanguage.TYPESCRIPT,
        '.java': CodeLanguage.JAVA,
        '.go': CodeLanguage.GO,
        '.rs': CodeLanguage.RUST,
        '.cpp': CodeLanguage.CPP,
        '.cc': CodeLanguage.CPP,
        '.cxx': CodeLanguage.CPP,
        '.c': CodeLanguage.C,
        '.cs': CodeLanguage.CSHARP,
        '.php': CodeLanguage.PHP,
        '.rb': CodeLanguage.RUBY,
    }
    
    # Получаем расширение файла
    extension = '.' + filename.split('.')[-1] if '.' in filename else ''
    return extension_map.get(extension.lower(), CodeLanguage.OTHER)


def create_code_file(filename: str, content: str, auto_detect_language: bool = True) -> CodeFile:
    """Создает объект CodeFile с автоматическим определением языка"""
    if auto_detect_language:
        language = get_language_from_extension(filename)
    else:
        language = CodeLanguage.OTHER
    
    return CodeFile(
        filename=filename,
        content=content,
        language=language,
        size_bytes=len(content.encode('utf-8')),
        last_modified=datetime.now()
    )


def get_default_documentation_request(
    code_input: Union[CodeFile, CodeRepository, str], 
    doc_type: DocumentationType = DocumentationType.README
) -> DocumentationRequest:
    """Создает запрос на документацию с настройками по умолчанию"""
    return DocumentationRequest(
        code_input=code_input,
        documentation_type=doc_type,
        target_audience="developers",
        detail_level="detailed",
        include_examples=True,
        include_installation=True,
        include_api_reference=True
    ) 