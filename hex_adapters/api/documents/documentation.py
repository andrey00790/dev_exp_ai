import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from domain.integration.documentation_service import (
    DocumentationServiceInterface, get_documentation_service)
from models.base import BaseResponse
from models.documentation import (DOCUMENTATION_CAPABILITIES, CodeAnalysis,
                                  CodeAnalysisRequest, CodeFile, CodeLanguage,
                                  DocumentationRequest, DocumentationResponse,
                                  DocumentationType)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/documentation/generate",
    response_model=DocumentationResponse,
    summary="Generate Code Documentation",
    description="Генерирует документацию по коду с использованием AI",
)
async def generate_documentation(
    request: DocumentationRequest,
    service: DocumentationServiceInterface = Depends(get_documentation_service),
) -> DocumentationResponse:
    """
    Генерирует документацию по коду с помощью AI.

    Поддерживает различные типы документации:
    - API документация
    - README файлы
    - Техническая спецификация
    - Руководство пользователя
    - Комментарии к коду
    """
    try:
        result = await service.generate_documentation(request)
        logger.info(
            f"Generated {request.documentation_type.value} documentation successfully"
        )
        return result

    except Exception as e:
        logger.error(f"Documentation generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка генерации документации: {str(e)}",
        )


@router.post(
    "/documentation/analyze",
    response_model=CodeAnalysis,
    summary="Analyze Code",
    description="Анализирует код без генерации документации",
)
async def analyze_code(
    request: CodeAnalysisRequest,
    service: DocumentationServiceInterface = Depends(get_documentation_service),
) -> CodeAnalysis:
    """
    Анализирует код и возвращает детальную информацию:
    - Функции и классы
    - Зависимости
    - Архитектурные паттерны
    - Проблемы безопасности
    - Оценка сложности
    """
    try:
        result = await service.analyze_code(request)
        logger.info(
            f"Code analysis completed: {len(result.functions)} functions, {len(result.classes)} classes found"
        )
        return result

    except Exception as e:
        logger.error(f"Code analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка анализа кода: {str(e)}",
        )


@router.get(
    "/documentation/capabilities",
    response_model=Dict[str, Any],
    summary="Get Documentation Capabilities",
    description="Возвращает список поддерживаемых возможностей генерации документации",
)
async def get_capabilities(
    service: DocumentationServiceInterface = Depends(get_documentation_service),
) -> Dict[str, Any]:
    """
    Возвращает информацию о возможностях системы генерации документации:
    - Поддерживаемые языки программирования
    - Типы документации
    - Форматы вывода
    - Функции анализа
    """
    try:
        capabilities = await service.get_supported_capabilities()
        return capabilities

    except Exception as e:
        logger.error(f"Failed to get capabilities: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения возможностей: {str(e)}",
        )


@router.get(
    "/documentation/templates",
    response_model=list,
    summary="Get Documentation Templates",
    description="Возвращает доступные шаблоны документации",
)
async def get_templates(
    service: DocumentationServiceInterface = Depends(get_documentation_service),
) -> list:
    """
    Возвращает список доступных шаблонов документации с описанием:
    - Назначение шаблона
    - Рекомендуемые случаи использования
    - Структура документа
    """
    try:
        templates = await service.get_documentation_templates()
        return templates

    except Exception as e:
        logger.error(f"Failed to get templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения шаблонов: {str(e)}",
        )


@router.post(
    "/documentation/quick-generate",
    response_model=DocumentationResponse,
    summary="Quick Documentation Generation",
    description="Быстрая генерация документации для простого кода",
)
async def quick_generate_documentation(
    code: str,
    documentation_type: DocumentationType = DocumentationType.README,
    target_audience: str = "developers",
    service: DocumentationServiceInterface = Depends(get_documentation_service),
) -> DocumentationResponse:
    """
    Упрощенный endpoint для быстрой генерации документации.

    Принимает код как простую строку и генерирует документацию
    с настройками по умолчанию.
    """
    try:
        # Создаем запрос из простой строки кода
        request = DocumentationRequest(
            documentation_type=documentation_type,
            code_input=code,
            target_audience=target_audience,
            detail_level="detailed",
            include_examples=True,
        )

        result = await service.generate_documentation(request)
        logger.info(f"Quick generated {documentation_type.value} documentation")
        return result

    except Exception as e:
        logger.error(f"Quick documentation generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка быстрой генерации документации: {str(e)}",
        )


@router.get(
    "/documentation/examples",
    response_model=Dict[str, Any],
    summary="Get Documentation Examples",
    description="Возвращает примеры запросов для генерации документации",
)
async def get_documentation_examples() -> Dict[str, Any]:
    """
    Возвращает примеры использования API генерации документации
    для разных типов кода и документации.
    """
    return {
        "api_documentation_example": {
            "documentation_type": "api_docs",
            "code_input": {
                "filename": "main.py",
                "content": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef read_root():\n    return {'Hello': 'World'}",
                "language": "python",
            },
            "target_audience": "developers",
            "detail_level": "detailed",
            "include_examples": True,
        },
        "readme_example": {
            "documentation_type": "readme",
            "code_input": "# Simple Python calculator\ndef add(a, b):\n    return a + b\n\ndef subtract(a, b):\n    return a - b",
            "target_audience": "users",
            "detail_level": "brief",
        },
        "supported_languages": [lang.value for lang in CodeLanguage],
        "documentation_types": [doc_type.value for doc_type in DocumentationType],
        "tips": [
            "Предоставьте полный контекст кода для лучших результатов",
            "Укажите целевую аудиторию для оптимизации тона документации",
            "Используйте detail_level='comprehensive' для максимальной детализации",
            "Включите include_examples=True для примеров использования",
        ],
    }
