# 📄 Code Documentation API - Руководство по генерации документации

**Версия:** 1.0  
**Дата:** 28 декабря 2024  
**Статус:** Production Ready  

---

## 🎯 Обзор

API генерации документации позволяет автоматически создавать высококачественную документацию для кода на 13+ языках программирования. Использует AI для анализа кода и создания понятной документации.

## 🌟 Основные возможности

- **📝 Автоматическая генерация README** - Создание README файлов с описанием проекта
- **🔧 API документация** - Генерация документации для REST API и GraphQL
- **📋 Технические спецификации** - Детальные tech specs для архитектуры
- **👥 Пользовательские руководства** - Инструкции для конечных пользователей
- **🎨 Форматы вывода** - Markdown, reStructuredText, HTML
- **🔍 Анализ кода** - Автоматический анализ структуры и зависимостей

## 🛠️ Поддерживаемые языки

| Язык | Поддержка | Особенности |
|------|-----------|-------------|
| Python | ✅ Полная | Docstrings, type hints, decorators |
| JavaScript | ✅ Полная | JSDoc, ES6+, Node.js |
| TypeScript | ✅ Полная | Interfaces, generics, decorators |
| Java | ✅ Полная | Annotations, Javadoc |
| Go | ✅ Полная | Packages, interfaces |
| Rust | ✅ Полная | Traits, lifetimes |
| C++ | ✅ Полная | Headers, templates |
| C# | ✅ Полная | XML docs, attributes |
| PHP | ✅ Полная | PHPDoc, namespaces |
| Ruby | ✅ Полная | Modules, gems |
| Swift | ✅ Полная | Protocols, extensions |
| Kotlin | ✅ Полная | Coroutines, extensions |
| Scala | ✅ Полная | Traits, implicits |

---

## 📡 API Endpoints

### 🔧 Основные endpoints

#### POST `/api/v1/documents/generate`
Генерация документации для кода

**Request:**
```json
{
  "code": "string",
  "language": "python",
  "doc_type": "readme",
  "target_audience": "developers",
  "detail_level": "detailed",
  "output_format": "markdown",
  "include_examples": true,
  "project_context": "Optional project description"
}
```

**Response:**
```json
{
  "generated_doc": "string",
  "doc_type": "readme",
  "language": "python",
  "word_count": 1250,
  "generation_time": 2.3,
  "quality_score": 0.92,
  "sections": [
    {
      "title": "Installation",
      "content": "...",
      "word_count": 120
    }
  ],
  "metadata": {
    "functions_documented": 15,
    "classes_documented": 3,
    "complexity_score": 0.7
  }
}
```

#### POST `/api/v1/documents/generate/file`
Генерация документации для файла

**Request (multipart/form-data):**
```
file: <code_file>
doc_type: readme
language: python
target_audience: developers
detail_level: detailed
```

**Response:** Аналогично `/generate`

#### POST `/api/v1/documents/generate/project`
Генерация документации для всего проекта

**Request:**
```json
{
  "project_path": "/path/to/project",
  "doc_types": ["readme", "api_docs", "user_guide"],
  "languages": ["python", "javascript"],
  "output_format": "markdown",
  "include_architecture": true,
  "include_setup_guide": true
}
```

**Response:**
```json
{
  "documents": [
    {
      "doc_type": "readme",
      "content": "...",
      "file_path": "README.md"
    },
    {
      "doc_type": "api_docs",
      "content": "...",
      "file_path": "docs/API.md"
    }
  ],
  "project_analysis": {
    "total_files": 45,
    "languages_detected": ["python", "javascript"],
    "architecture_complexity": "medium",
    "dependencies": ["fastapi", "react"]
  },
  "generation_summary": {
    "total_docs": 3,
    "total_words": 5680,
    "generation_time": 12.5
  }
}
```

### 📊 Дополнительные endpoints

#### GET `/api/v1/documents/templates`
Получение доступных шаблонов документации

**Response:**
```json
{
  "templates": [
    {
      "id": "readme_basic",
      "name": "Basic README",
      "description": "Simple README template",
      "sections": ["description", "installation", "usage"]
    },
    {
      "id": "api_docs_rest",
      "name": "REST API Documentation",
      "description": "Complete REST API documentation",
      "sections": ["overview", "endpoints", "examples", "errors"]
    }
  ]
}
```

#### GET `/api/v1/documents/examples/{language}`
Получение примеров документации для языка

**Response:**
```json
{
  "language": "python",
  "examples": [
    {
      "type": "readme",
      "title": "FastAPI Application README",
      "preview": "# FastAPI Application\n\nThis is a modern..."
    }
  ]
}
```

---

## 🎯 Типы документации

### 📝 README файлы (`readme`)
Создание README файлов с:
- Описанием проекта
- Инструкциями по установке
- Примерами использования
- Информацией о вкладе в проект

### 🔧 API документация (`api_docs`)
Генерация документации для API:
- REST API endpoints
- GraphQL schemas
- SDK документация
- Примеры запросов/ответов

### 📋 Технические спецификации (`tech_specs`)
Детальные технические документы:
- Архитектурные решения
- Технические требования
- Диаграммы компонентов
- Спецификации интерфейсов

### 👥 Пользовательские руководства (`user_guide`)
Инструкции для конечных пользователей:
- Пошаговые руководства
- Часто задаваемые вопросы
- Примеры использования
- Устранение неполадок

### 🎨 Руководства по стилю (`style_guide`)
Стандарты кодирования:
- Правила оформления кода
- Naming conventions
- Лучшие практики
- Code review guidelines

---

## 📊 Параметры генерации

### 🎯 Целевая аудитория (`target_audience`)
- `developers` - Разработчики (технические детали)
- `users` - Конечные пользователи (простой язык)
- `mixed` - Смешанная аудитория
- `technical_writers` - Технические писатели

### 📏 Уровень детализации (`detail_level`)
- `brief` - Краткое описание
- `standard` - Стандартная детализация
- `detailed` - Подробная документация
- `comprehensive` - Исчерпывающая документация

### 📄 Формат вывода (`output_format`)
- `markdown` - Markdown (.md)
- `rst` - reStructuredText (.rst)
- `html` - HTML (.html)
- `docx` - Microsoft Word (.docx)
- `pdf` - PDF (.pdf)

---

## 🔍 Примеры использования

### Python FastAPI Application

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get(\"/\")\ndef read_root():\n    return {\"Hello\": \"World\"}",
    "language": "python",
    "doc_type": "readme",
    "target_audience": "developers",
    "detail_level": "detailed"
  }'
```

**Generated README:**
```markdown
# FastAPI Application

A modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints.

## Features

- **Fast**: Very high performance, on par with NodeJS and Go
- **Fast to code**: Increase the speed to develop features by about 200% to 300%
- **Fewer bugs**: Reduce about 40% of human (developer) induced errors
- **Intuitive**: Great editor support with autocompletion everywhere
- **Easy**: Designed to be easy to use and learn
- **Short**: Minimize code duplication

## Installation

```bash
pip install fastapi uvicorn
```

## Usage

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

## Running the Application

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## License

MIT License
```

### React Component Documentation

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "import React from \"react\";\n\ninterface Props {\n  name: string;\n  age?: number;\n}\n\nconst UserCard: React.FC<Props> = ({ name, age }) => {\n  return (\n    <div>\n      <h2>{name}</h2>\n      {age && <p>Age: {age}</p>}\n    </div>\n  );\n};",
    "language": "typescript",
    "doc_type": "api_docs",
    "target_audience": "developers"
  }'
```

**Generated Documentation:**
```markdown
# UserCard Component

A React functional component for displaying user information.

## Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | Yes | The user's name |
| `age` | number | No | The user's age (optional) |

## Usage

```tsx
import UserCard from './UserCard';

// Basic usage
<UserCard name="John Doe" />

// With age
<UserCard name="Jane Smith" age={25} />
```

## Features

- TypeScript support with strict typing
- Conditional rendering for optional age
- Clean, semantic HTML structure
- Responsive design ready

## Styling

The component uses semantic HTML elements that can be styled with CSS:

```css
.user-card h2 {
  color: #333;
  margin-bottom: 0.5rem;
}

.user-card p {
  color: #666;
  font-size: 0.9rem;
}
```
```

---

## 🎨 Frontend интеграция

### React компонент

```tsx
import React, { useState } from 'react';
import { generateDocumentation } from '../api/documentsApi';

interface CodeDocumentationProps {
  initialCode?: string;
  language?: string;
}

const CodeDocumentation: React.FC<CodeDocumentationProps> = ({
  initialCode = '',
  language = 'python'
}) => {
  const [code, setCode] = useState(initialCode);
  const [docType, setDocType] = useState('readme');
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const response = await generateDocumentation({
        code,
        language,
        doc_type: docType,
        target_audience: 'developers',
        detail_level: 'detailed'
      });
      setResult(response.generated_doc);
    } catch (error) {
      console.error('Documentation generation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="code-documentation">
      <div className="input-section">
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Paste your code here..."
          className="code-input"
        />
        <select
          value={docType}
          onChange={(e) => setDocType(e.target.value)}
          className="doc-type-select"
        >
          <option value="readme">README</option>
          <option value="api_docs">API Documentation</option>
          <option value="user_guide">User Guide</option>
        </select>
        <button
          onClick={handleGenerate}
          disabled={loading || !code.trim()}
          className="generate-btn"
        >
          {loading ? 'Generating...' : 'Generate Documentation'}
        </button>
      </div>
      
      {result && (
        <div className="result-section">
          <h3>Generated Documentation</h3>
          <pre className="documentation-result">{result}</pre>
        </div>
      )}
    </div>
  );
};

export default CodeDocumentation;
```

### API Client

```typescript
interface DocumentationRequest {
  code: string;
  language: string;
  doc_type: string;
  target_audience: string;
  detail_level: string;
  output_format?: string;
  include_examples?: boolean;
}

interface DocumentationResponse {
  generated_doc: string;
  doc_type: string;
  language: string;
  word_count: number;
  generation_time: number;
  quality_score: number;
  sections: Array<{
    title: string;
    content: string;
    word_count: number;
  }>;
  metadata: {
    functions_documented: number;
    classes_documented: number;
    complexity_score: number;
  };
}

export const generateDocumentation = async (
  request: DocumentationRequest
): Promise<DocumentationResponse> => {
  const response = await fetch('/api/v1/documents/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`
    },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    throw new Error(`Documentation generation failed: ${response.statusText}`);
  }

  return response.json();
};
```

---

## 🔧 Продвинутые возможности

### 🎯 Batch генерация

```bash
curl -X POST "http://localhost:8000/api/v1/documents/generate/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "files": [
      {
        "path": "src/main.py",
        "doc_type": "api_docs"
      },
      {
        "path": "src/utils.py",
        "doc_type": "readme"
      }
    ],
    "global_settings": {
      "target_audience": "developers",
      "detail_level": "detailed",
      "output_format": "markdown"
    }
  }'
```

### 🔍 Анализ качества

```bash
curl -X POST "http://localhost:8000/api/v1/documents/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "documentation": "# My Project\n\nThis is a sample project...",
    "analysis_type": "quality_check"
  }'
```

**Response:**
```json
{
  "quality_score": 0.85,
  "completeness": 0.9,
  "clarity": 0.8,
  "structure": 0.9,
  "suggestions": [
    "Add more code examples",
    "Include troubleshooting section",
    "Add API reference links"
  ],
  "metrics": {
    "word_count": 1200,
    "readability_score": 7.2,
    "sections_count": 6
  }
}
```

### 📊 Шаблоны документации

```bash
curl -X GET "http://localhost:8000/api/v1/documents/templates?language=python&doc_type=readme"
```

**Response:**
```json
{
  "templates": [
    {
      "id": "python_package_readme",
      "name": "Python Package README",
      "sections": [
        "title",
        "description",
        "installation",
        "usage",
        "api_reference",
        "contributing",
        "license"
      ],
      "example_url": "/api/v1/documents/templates/python_package_readme/example"
    }
  ]
}
```

---

## 📈 Метрики и аналитика

### 📊 Статистика генерации

```bash
curl -X GET "http://localhost:8000/api/v1/documents/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "total_documents": 1250,
  "languages": {
    "python": 450,
    "javascript": 320,
    "typescript": 280,
    "java": 200
  },
  "doc_types": {
    "readme": 500,
    "api_docs": 400,
    "user_guide": 250,
    "tech_specs": 100
  },
  "average_quality_score": 0.87,
  "average_generation_time": 2.3
}
```

### 🎯 Персональная аналитика

```bash
curl -X GET "http://localhost:8000/api/v1/documents/user/analytics" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "user_stats": {
    "documents_generated": 45,
    "favorite_language": "python",
    "favorite_doc_type": "readme",
    "total_words_generated": 25680,
    "average_quality_score": 0.91
  },
  "recent_activity": [
    {
      "date": "2024-12-28",
      "doc_type": "readme",
      "language": "python",
      "quality_score": 0.95
    }
  ],
  "recommendations": [
    "Try generating API documentation for better code coverage",
    "Consider using detailed level for more comprehensive docs"
  ]
}
```

---

## 🚀 Лучшие практики

### ✅ Рекомендации по использованию

1. **Качественный код** - Предоставляйте хорошо структурированный код
2. **Контекст проекта** - Указывайте описание проекта для лучших результатов
3. **Правильный язык** - Указывайте точный язык программирования
4. **Целевая аудитория** - Выбирайте подходящую аудиторию
5. **Итеративный подход** - Генерируйте документацию поэтапно

### ⚠️ Ограничения

- **Размер кода**: Максимум 50KB на запрос
- **Время генерации**: До 30 секунд для сложных проектов
- **Качество**: Зависит от качества исходного кода
- **Языки**: Поддерживаются только указанные 13 языков

---

## 🐛 Troubleshooting

### Частые проблемы

#### 1. "Language not supported"
```json
{
  "error": "Language 'pascal' not supported",
  "supported_languages": ["python", "javascript", "typescript", ...]
}
```

**Решение**: Используйте один из поддерживаемых языков

#### 2. "Code too large"
```json
{
  "error": "Code size exceeds limit",
  "max_size_kb": 50,
  "current_size_kb": 75
}
```

**Решение**: Разделите код на части или используйте batch API

#### 3. "Generation timeout"
```json
{
  "error": "Documentation generation timed out",
  "timeout_seconds": 30
}
```

**Решение**: Упростите код или используйте менее детальный уровень

### 🔧 Диагностика

```bash
# Проверка статуса сервиса
curl -X GET "http://localhost:8000/api/v1/documents/health"

# Проверка поддерживаемых языков
curl -X GET "http://localhost:8000/api/v1/documents/supported-languages"

# Тест с минимальным кодом
curl -X POST "http://localhost:8000/api/v1/documents/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello World\")",
    "language": "python",
    "doc_type": "readme"
  }'
```

---

## 🔗 Полезные ссылки

- [OpenAPI Specification](http://localhost:8000/docs#tag/Document-Generation)
- [Frontend Integration Example](../frontend/src/pages/CodeDocumentation.tsx)
- [API Client TypeScript](../frontend/src/api/documentsApi.ts)
- [Testing Guide](../tests/integration/test_document_generation.py)

---

**📝 Примечание**: API генерации документации постоянно улучшается. Следите за обновлениями и новыми возможностями в [релизах](https://github.com/your-repo/releases). 