from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import os


class CodeLanguage(str, Enum):
    """Поддерживаемые языки программирования."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"
    PHP = "php"
    RUBY = "ruby"
    KOTLIN = "kotlin"
    SWIFT = "swift"
    OTHER = "other"


class DocumentationType(str, Enum):
    """Типы документации для генерации."""
    API_DOCS = "api_docs"                    # API документация
    CODE_COMMENTS = "code_comments"          # Комментарии к коду
    README = "readme"                        # README файл
    TECHNICAL_SPEC = "technical_spec"        # Техническая спецификация
    USER_GUIDE = "user_guide"               # Руководство пользователе
    ARCHITECTURE_DOC = "architecture_doc"    # Архитектурная документация
    CHANGELOG = "changelog"                  # История изменений
    DEPLOYMENT_GUIDE = "deployment_guide"   # Руководство по развертыванию


class CodeFile(BaseModel):
    """Представление файла с кодом."""
    filename: str
    content: str
    language: CodeLanguage
    path: Optional[str] = None              # Относительный путь к файлу
    size_bytes: Optional[int] = None
    
    @field_validator('size_bytes', mode='before')
    def set_size_bytes(cls, v, values):
        if v is None and 'content' in values:
            return len(values['content'].encode('utf-8'))
        return v


class CodeRepository(BaseModel):
    """Представление репозитория или проекта."""
    name: str
    description: Optional[str] = None
    files: List[CodeFile] = []
    main_language: Optional[CodeLanguage] = None
    framework: Optional[str] = None         # React, Django, Spring, etc.
    dependencies: List[str] = []            # package.json, requirements.txt, etc.
    size_bytes: Optional[int] = None
    
    
    @field_validator('size_bytes', mode='before')
    def validate_size_bytes(cls, v):
        pass

    @field_validator('main_language', mode='before')
    def validate_main_language(cls, v, values):
        pass


class DocumentationRequest(BaseModel):
    """Запрос на генерацию документации."""
    documentation_type: DocumentationType
    code_input: Union[CodeFile, CodeRepository, str]  # Код или путь к репозиторию
    target_audience: str = Field(
        default="developers",
        description="Целевая аудитория: developers, users, stakeholders, etc."
    )
    detail_level: str = Field(
        default="detailed",
        description="Уровень детализации: brief, detailed, comprehensive"
    )
    include_examples: bool = True           # Включать примеры использования
    include_diagrams: bool = False          # Включать диаграммы (Mermaid)
    output_format: str = Field(
        default="markdown",
        description="Формат вывода: markdown, html, rst, docx"
    )
    custom_requirements: Optional[str] = None  # Дополнительные требования
    user_id: Optional[str] = None


class CodeAnalysis(BaseModel):
    """Результат анализа кода."""
    functions: List[Dict[str, Any]] = []     # Найденные функции/методы
    classes: List[Dict[str, Any]] = []       # Найденные классы
    modules: List[Dict[str, Any]] = []       # Модули/пакеты
    dependencies: List[str] = []             # Внешние зависимости
    complexity_score: Optional[float] = None # Оценка сложности кода
    architecture_patterns: List[str] = []    # Обнаруженные паттерны
    security_concerns: List[str] = []        # Потенциальные проблемы безопасности
    performance_notes: List[str] = []        # Заметки о производительности


class DocumentationSection(BaseModel):
    """Секция документации."""
    title: str
    content: str
    order: int
    subsections: List['DocumentationSection'] = []
    section_type: str = "general"           # overview, api, examples, etc.
    
    
class GeneratedDocumentation(BaseModel):
    """Сгенерированная документация."""
    id: Optional[str] = None
    request_id: Optional[str] = None
    title: str
    summary: str
    sections: List[DocumentationSection]
    full_content: str                       # Полный контент в указанном формате
    code_analysis: Optional[CodeAnalysis] = None
    metadata: Dict[str, Any] = {}
    suggestions: List[str] = []             # Предложения по улучшению кода
    created_at: Optional[datetime] = None
    
    
class DocumentationResponse(BaseModel):
    """Ответ на запрос генерации документации."""
    documentation: GeneratedDocumentation
    message: str = "Документация успешно сгенерирована"
    generation_time_seconds: Optional[float] = None
    analysis_stats: Dict[str, Any] = {}     # Статистика анализа кода


class CodeAnalysisRequest(BaseModel):
    """Запрос на анализ кода без генерации документации."""
    code_input: Union[CodeFile, CodeRepository, str]
    analysis_depth: str = Field(
        default="standard",
        description="Глубина анализа: quick, standard, deep"
    )
    include_security_check: bool = True
    include_performance_analysis: bool = True


class DocumentationTemplate(BaseModel):
    """Шаблон документации."""
    name: str
    description: str
    documentation_type: DocumentationType
    sections: List[str]                     # Список обязательных секций
    target_audience: str
    example_content: Optional[str] = None


class DocumentationExamples(BaseModel):
    """Примеры для различных типов документации."""
    api_docs_example: str
    readme_example: str
    technical_spec_example: str
    code_comments_example: str
    
    
# Обновляем рекурсивные модели
DocumentationSection.model_rebuild()


# Константы для валидации
SUPPORTED_OUTPUT_FORMATS = ["markdown", "html", "rst", "docx", "pdf"]
DETAIL_LEVELS = ["brief", "detailed", "comprehensive"]
TARGET_AUDIENCES = ["developers", "users", "stakeholders", "technical_writers", "management"]

# Мета-информация о возможностях системы
DOCUMENTATION_CAPABILITIES = {
    "supported_languages": [lang.value for lang in CodeLanguage],
    "documentation_types": [doc_type.value for doc_type in DocumentationType],
    "output_formats": SUPPORTED_OUTPUT_FORMATS,
    "features": [
        "Автоматический анализ кода",
        "Генерация API документации",
        "Создание README файлов",
        "Техническая спецификация",
        "Архитектурная документация", 
        "Анализ безопасности кода",
        "Оценка производительности",
        "Диаграммы и схемы",
        "Множественные форматы вывода",
        "Настраиваемые шаблоны"
    ]
} 