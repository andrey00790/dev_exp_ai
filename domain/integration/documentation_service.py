import ast
import logging
import re
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from models.documentation import (DOCUMENTATION_CAPABILITIES, CodeAnalysis,
                                  CodeAnalysisRequest, CodeFile, CodeLanguage,
                                  CodeRepository, DocumentationRequest,
                                  DocumentationResponse, DocumentationSection,
                                  DocumentationType, GeneratedDocumentation)

logger = logging.getLogger(__name__)


class DocumentationServiceInterface(ABC):
    """Interface for documentation generation service."""

    @abstractmethod
    async def generate_documentation(
        self, request: DocumentationRequest
    ) -> DocumentationResponse:
        """Генерирует документацию по коду."""
        pass

    @abstractmethod
    async def analyze_code(self, request: CodeAnalysisRequest) -> CodeAnalysis:
        """Анализирует код без генерации документации."""
        pass

    @abstractmethod
    async def get_supported_capabilities(self) -> Dict[str, Any]:
        """Возвращает список поддерживаемых возможностей."""
        pass

    @abstractmethod
    async def get_documentation_templates(self) -> List[Dict[str, Any]]:
        """Возвращает доступные шаблоны документации."""
        pass


class DocumentationService(DocumentationServiceInterface):
    """Основной сервис для генерации документации по коду."""

    def __init__(self):
        """Инициализация сервиса документации."""
        self._generated_docs: Dict[str, GeneratedDocumentation] = {}
        logger.info("Documentation Service initialized")

    async def generate_documentation(
        self, request: DocumentationRequest
    ) -> DocumentationResponse:
        """Генерирует документацию по коду с использованием LLM."""
        start_time = time.time()

        try:
            # 1. Анализируем код
            code_analysis = await self._perform_code_analysis(request.code_input)

            # 2. Генерируем документацию
            documentation = await self._generate_documentation_with_llm(
                request, code_analysis
            )

            # 3. Сохраняем результат
            doc_id = str(uuid.uuid4())
            documentation.id = doc_id
            documentation.created_at = datetime.now()
            self._generated_docs[doc_id] = documentation

            generation_time = time.time() - start_time

            return DocumentationResponse(
                documentation=documentation,
                message=f"Документация успешно сгенерирована для {request.documentation_type.value}",
                generation_time_seconds=round(generation_time, 2),
                analysis_stats={
                    "functions_analyzed": len(code_analysis.functions),
                    "classes_analyzed": len(code_analysis.classes),
                    "modules_analyzed": len(code_analysis.modules),
                    "dependencies_found": len(code_analysis.dependencies),
                    "complexity_score": code_analysis.complexity_score,
                    "sections_generated": len(documentation.sections),
                },
            )

        except Exception as e:
            logger.error(f"Documentation generation failed: {str(e)}")
            raise Exception(f"Ошибка генерации документации: {str(e)}")

    async def analyze_code(self, request: CodeAnalysisRequest) -> CodeAnalysis:
        """Анализирует код без генерации документации."""
        try:
            return await self._perform_code_analysis(request.code_input)
        except Exception as e:
            logger.error(f"Code analysis failed: {str(e)}")
            raise Exception(f"Ошибка анализа кода: {str(e)}")

    async def get_supported_capabilities(self) -> Dict[str, Any]:
        """Возвращает список поддерживаемых возможностей."""
        return DOCUMENTATION_CAPABILITIES

    async def get_documentation_templates(self) -> List[Dict[str, Any]]:
        """Возвращает доступные шаблоны документации."""
        return [
            {
                "name": "API Documentation",
                "type": "api_docs",
                "description": "Comprehensive API documentation with examples",
                "sections": [
                    "Overview",
                    "Authentication",
                    "Endpoints",
                    "Models",
                    "Examples",
                ],
                "best_for": ["REST APIs", "GraphQL APIs", "Web Services"],
            },
            {
                "name": "README Template",
                "type": "readme",
                "description": "Standard README with installation and usage",
                "sections": [
                    "Description",
                    "Installation",
                    "Usage",
                    "Contributing",
                    "License",
                ],
                "best_for": ["Open Source Projects", "Libraries", "Applications"],
            },
        ]

    async def _perform_code_analysis(
        self, code_input: Union[CodeFile, CodeRepository, str]
    ) -> CodeAnalysis:
        """Выполняет анализ кода."""
        if isinstance(code_input, str):
            return await self._analyze_code_string(code_input)
        elif isinstance(code_input, CodeFile):
            return await self._analyze_single_file(code_input)
        elif isinstance(code_input, CodeRepository):
            return await self._analyze_repository(code_input)
        else:
            raise ValueError("Неподдерживаемый тип кода для анализа")

    async def _analyze_code_string(self, code: str) -> CodeAnalysis:
        """Анализирует строку с кодом."""
        language = self._detect_language_from_content(code)
        code_file = CodeFile(filename="code_snippet", content=code, language=language)
        return await self._analyze_single_file(code_file)

    async def _analyze_single_file(self, code_file: CodeFile) -> CodeAnalysis:
        """Анализирует один файл с кодом."""
        if code_file.language == CodeLanguage.PYTHON:
            return await self._analyze_python_code(code_file.content)
        else:
            return await self._basic_code_analysis(code_file.content)

    async def _analyze_repository(self, repository: CodeRepository) -> CodeAnalysis:
        """Анализирует весь репозиторий."""
        combined_analysis = CodeAnalysis()
        for file in repository.files:
            file_analysis = await self._analyze_single_file(file)
            combined_analysis.functions.extend(file_analysis.functions)
            combined_analysis.classes.extend(file_analysis.classes)
            combined_analysis.dependencies.extend(file_analysis.dependencies)
        return combined_analysis

    async def _analyze_python_code(self, code: str) -> CodeAnalysis:
        """Анализирует Python код."""
        analysis = CodeAnalysis()

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "line_number": node.lineno,
                        "docstring": ast.get_docstring(node),
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                    }
                    analysis.functions.append(func_info)

                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "line_number": node.lineno,
                        "docstring": ast.get_docstring(node),
                        "methods": [
                            n.name for n in node.body if isinstance(n, ast.FunctionDef)
                        ],
                    }
                    analysis.classes.append(class_info)

                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            analysis.dependencies.append(alias.name)
                    else:
                        if node.module:
                            analysis.dependencies.append(node.module)

            # Определяем архитектурные паттерны
            analysis.architecture_patterns = self._detect_python_patterns(code)

            # Проверяем безопасность
            analysis.security_concerns = self._check_python_security(code)

            # Заметки о производительности
            analysis.performance_notes = self._check_python_performance(code)

            # Вычисляем общую сложность как среднее по функциям
            if analysis.functions:
                complexities = [f.get("complexity", 1) for f in analysis.functions]
                analysis.complexity_score = sum(complexities) / len(complexities)
            else:
                analysis.complexity_score = 1.0

        except SyntaxError as e:
            logger.warning(f"Python syntax error during analysis: {e}")
            return await self._basic_code_analysis(code)

        return analysis

    async def _basic_code_analysis(self, code: str) -> CodeAnalysis:
        """Базовый анализ для неподдерживаемых языков."""
        analysis = CodeAnalysis()
        lines = code.split("\n")
        analysis.modules.append(
            {
                "name": "code_module",
                "lines_of_code": len([line for line in lines if line.strip()]),
            }
        )
        analysis.complexity_score = min(len(lines) / 10, 10.0)
        return analysis

    def _detect_language_from_content(self, code: str) -> CodeLanguage:
        """Определяет язык программирования по содержимому."""
        # Простая эвристика с улучшенным распознаванием Python
        code_lower = code.lower()

        # Python паттерны
        python_patterns = [
            "def ",
            "class ",
            "import ",
            "from ",
            "__init__",
            "self.",
            "elif ",
            "return ",
            '"""',
            "'''",
            "async def",
            "await ",
            "yield ",
            "lambda ",
        ]

        # JavaScript/TypeScript паттерны
        js_patterns = [
            "function ",
            "const ",
            "let ",
            "var ",
            "console.log",
            "=>",
            "require(",
            "exports.",
            "module.exports",
        ]

        # Java паттерны
        java_patterns = [
            "public class ",
            "private ",
            "protected ",
            "static ",
            "public static void main",
            "import java",
            "extends ",
            "implements ",
        ]

        # Go паттерны
        go_patterns = ["package ", "func ", "import (", "type ", "struct "]

        # Подсчитываем совпадения для каждого языка
        python_score = sum(1 for pattern in python_patterns if pattern in code_lower)
        js_score = sum(1 for pattern in js_patterns if pattern in code_lower)
        java_score = sum(1 for pattern in java_patterns if pattern in code_lower)
        go_score = sum(1 for pattern in go_patterns if pattern in code_lower)

        # TypeScript дополнительно проверяем
        ts_bonus = 0
        if "interface " in code or ": string" in code or ": number" in code:
            ts_bonus = 2

        # Определяем язык по максимальному счету
        scores = {
            CodeLanguage.PYTHON: python_score,
            CodeLanguage.JAVASCRIPT: js_score + (ts_bonus if ts_bonus < 2 else 0),
            CodeLanguage.TYPESCRIPT: js_score + ts_bonus,
            CodeLanguage.JAVA: java_score,
            CodeLanguage.GO: go_score,
        }

        max_score = max(scores.values())
        if max_score == 0:
            return CodeLanguage.OTHER

        # Возвращаем язык с максимальным счетом
        for lang, score in scores.items():
            if score == max_score:
                return lang

        return CodeLanguage.OTHER

    def _detect_python_patterns(self, code: str) -> List[str]:
        """Определяет архитектурные паттерны в Python коде."""
        patterns = []

        if "FastAPI" in code or "@app.get" in code:
            patterns.append("FastAPI")
        if "Django" in code or "django.db" in code:
            patterns.append("Django")
        if "Flask" in code or "@app.route" in code:
            patterns.append("Flask")
        if "async def" in code:
            patterns.append("Async/Await")
        if "pydantic" in code or "BaseModel" in code:
            patterns.append("Pydantic Models")
        if "SQLAlchemy" in code:
            patterns.append("SQLAlchemy ORM")

        return patterns

    def _check_python_security(self, code: str) -> List[str]:
        """Проверяет потенциальные проблемы безопасности в Python коде."""
        concerns = []

        if "eval(" in code:
            concerns.append("Использование eval() может быть небезопасным")
        if "exec(" in code:
            concerns.append("Использование exec() может быть небезопасным")
        if "os.system(" in code:
            concerns.append("Прямое выполнение системных команд")
        if "subprocess.call(" in code and "shell=True" in code:
            concerns.append("Выполнение команд через shell может быть небезопасным")
        if "pickle.loads(" in code:
            concerns.append("Десериализация pickle может быть небезопасной")

        return concerns

    def _check_python_performance(self, code: str) -> List[str]:
        """Проверяет потенциальные проблемы производительности."""
        notes = []

        if ".append(" in code and "for " in code:
            notes.append(
                "Рассмотрите использование list comprehension для лучшей производительности"
            )
        if "pandas" in code and ".iterrows()" in code:
            notes.append("iterrows() медленный, рассмотрите векторизацию")
        if "time.sleep(" in code:
            notes.append("Используйте asyncio.sleep() в асинхронном коде")

        return notes

    async def _generate_documentation_with_llm(
        self, request: DocumentationRequest, code_analysis: CodeAnalysis
    ) -> GeneratedDocumentation:
        """Генерирует документацию с помощью LLM."""

        try:
            # Используем LLM для генерации документации
            from domain.core.llm_generation_service import LLMGenerationService

            llm_service = LLMGenerationService()

            # Подготавливаем контекст для LLM
            context = self._prepare_llm_context(request, code_analysis)

            # Генерируем документацию
            doc_content = await llm_service.generate_code_documentation(
                request.documentation_type,
                context,
                request.target_audience,
                request.detail_level,
            )

            # Парсим результат
            documentation = self._parse_llm_documentation(
                doc_content, request, code_analysis
            )
            return documentation

        except Exception as e:
            logger.warning(f"LLM documentation generation failed: {e}")
            # Fallback на шаблонную генерацию
            return await self._generate_fallback_documentation(request, code_analysis)

    def _prepare_llm_context(
        self, request: DocumentationRequest, analysis: CodeAnalysis
    ) -> str:
        """Подготавливает контекст для LLM."""
        context_parts = []

        if isinstance(request.code_input, CodeFile):
            context_parts.append(f"Файл: {request.code_input.filename}")
            context_parts.append(f"Язык: {request.code_input.language.value}")

        if analysis.functions:
            func_names = [f["name"] for f in analysis.functions[:10]]
            context_parts.append(f"Функции: {', '.join(func_names)}")

        if analysis.classes:
            class_names = [c["name"] for c in analysis.classes[:10]]
            context_parts.append(f"Классы: {', '.join(class_names)}")

        context_parts.append(f"Тип документации: {request.documentation_type.value}")
        context_parts.append(f"Аудитория: {request.target_audience}")

        return "\n".join(context_parts)

    def _parse_llm_documentation(
        self, content: str, request: DocumentationRequest, analysis: CodeAnalysis
    ) -> GeneratedDocumentation:
        """Парсит документацию от LLM в структурированный формат."""

        sections = []
        lines = content.split("\n")
        current_section = None
        current_content = []
        section_order = 0

        for line in lines:
            if line.startswith("## "):
                if current_section:
                    sections.append(
                        DocumentationSection(
                            title=current_section,
                            content="\n".join(current_content).strip(),
                            order=section_order,
                        )
                    )
                    section_order += 1
                    current_content = []
                current_section = line[3:].strip()
            elif current_section:
                current_content.append(line)

        if current_section:
            sections.append(
                DocumentationSection(
                    title=current_section,
                    content="\n".join(current_content).strip(),
                    order=section_order,
                )
            )

        title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
        title = (
            title_match.group(1)
            if title_match
            else f"Документация ({request.documentation_type.value})"
        )

        return GeneratedDocumentation(
            title=title,
            summary="Автоматически сгенерированная документация",
            sections=sections,
            full_content=content,
            code_analysis=analysis,
            metadata={
                "documentation_type": request.documentation_type.value,
                "target_audience": request.target_audience,
                "generated_by": "AI Assistant Documentation Generator",
            },
            suggestions=[],
        )

    async def _generate_fallback_documentation(
        self, request: DocumentationRequest, analysis: CodeAnalysis
    ) -> GeneratedDocumentation:
        """Генерирует базовую документацию без LLM."""

        sections = []

        sections.append(
            DocumentationSection(
                title="Overview",
                content=f"Этот документ содержит {request.documentation_type.value} для предоставленного кода.",
                order=0,
            )
        )

        if analysis.functions:
            func_content = "\n".join(
                [
                    f"- **{func['name']}**: {func.get('docstring', 'Описание недоступно')}"
                    for func in analysis.functions[:10]
                ]
            )
            sections.append(
                DocumentationSection(title="Functions", content=func_content, order=1)
            )

        full_content = f"# Documentation\n\n"
        for section in sections:
            full_content += f"## {section.title}\n\n{section.content}\n\n"

        return GeneratedDocumentation(
            title="Generated Documentation",
            summary="Автоматически сгенерированная документация на основе анализа кода",
            sections=sections,
            full_content=full_content,
            code_analysis=analysis,
            metadata={"documentation_type": request.documentation_type.value},
            suggestions=[],
        )


# Global instance
_documentation_service_instance = None


def get_documentation_service() -> DocumentationServiceInterface:
    """Dependency injection для documentation service."""
    global _documentation_service_instance
    if _documentation_service_instance is None:
        _documentation_service_instance = DocumentationService()
    return _documentation_service_instance
