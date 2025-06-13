from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import uuid
from jinja2 import Environment, FileSystemLoader, Template

from models.generation import GenerationSession, UserAnswer, TaskType


class TemplateServiceInterface(ABC):
    """Interface for template service."""
    
    @abstractmethod
    async def generate_rfc_content(self, session: GenerationSession) -> str:
        """Генерирует содержимое RFC на основе сессии."""
        pass
    
    @abstractmethod
    async def get_template_variables(self, session: GenerationSession) -> Dict[str, Any]:
        """Извлекает переменные для заполнения шаблона."""
        pass


class RFCTemplateService(TemplateServiceInterface):
    """Сервис для генерации RFC документов на основе шаблонов."""
    
    def __init__(self, template_dir: str = "templates"):
        self.template_dir = Path(template_dir)
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
    
    async def generate_rfc_content(self, session: GenerationSession) -> str:
        """
        Генерирует полный RFC документ на основе шаблона и данных сессии.
        
        Использует лучшие практики от GitHub, Stripe, и других компаний.
        """
        try:
            # Получаем переменные для заполнения шаблона
            template_vars = await self.get_template_variables(session)
            
            # Загружаем шаблон
            template = self.env.get_template('rfc_template.md')
            
            # Заполняем шаблон
            rfc_content = template.render(**template_vars)
            
            return rfc_content
            
        except Exception as e:
            # Fallback на простой RFC в случае ошибки
            return await self._generate_fallback_rfc(session)
    
    async def get_template_variables(self, session: GenerationSession) -> Dict[str, Any]:
        """Извлекает и подготавливает переменные для RFC шаблона."""
        
        # Извлекаем ответы пользователя
        answers_dict = {answer.question_id: answer.answer for answer in session.answers}
        
        # Определяем тип задачи и соответствующий контекст
        task_context = await self._get_task_context(session.task_type, session.initial_request)
        
        # Базовые метаданные
        rfc_number = f"{datetime.now().year:04d}-{len(session.answers):03d}"
        
        # Генерируем содержимое на основе ответов и типа задачи
        content = await self._generate_content_sections(session, answers_dict, task_context)
        
        return {
            # Метаданные RFC
            'rfc_number': rfc_number,
            'title': await self._generate_title(session, answers_dict),
            'status': 'draft',
            'authors': [session.user_id or 'AI Assistant'],
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'updated_date': datetime.now().strftime('%Y-%m-%d'),
            'related_rfcs': [],
            'tags': await self._extract_tags(session, answers_dict),
            
            # Основное содержимое
            'summary': content['summary'],
            'context': content['context'],
            'problem_statement': content['problem_statement'],
            'current_state': content['current_state'],
            'business_goals': content['business_goals'],
            'goals': content['goals'],
            'non_goals': content['non_goals'],
            
            # Архитектурные секции
            'architecture_overview': content['architecture_overview'],
            'system_components': content['system_components'],
            'data_flow': content['data_flow'],
            'api_design': content['api_design'],
            'security_considerations': content['security_considerations'],
            'performance_scalability': content['performance_scalability'],
            
            # План реализации
            'implementation_plan': content['implementation_plan'],
            'phase_1_details': content['phase_1_details'],
            'phase_2_details': content['phase_2_details'],
            'phase_3_details': content['phase_3_details'],
            
            # Анализ решений
            'tradeoffs_alternatives': content['tradeoffs_alternatives'],
            'considered_alternatives': content['considered_alternatives'],
            'decision_rationale': content['decision_rationale'],
            
            # Оценка влияния
            'systems_affected': content['systems_affected'],
            'resource_requirements': content['resource_requirements'],
            'risk_analysis': content['risk_analysis'],
            'migration_strategy': content['migration_strategy'],
            
            # Дополнительные секции
            'monitoring_observability': content['monitoring_observability'],
            'testing_strategy': content['testing_strategy'],
            'documentation_requirements': content['documentation_requirements'],
            'success_metrics': content['success_metrics'],
            'timeline': content['timeline'],
            'next_steps': content['next_steps'],
            
            # Приложения
            'references': content['references'],
            'glossary': content['glossary'],
            'related_documents': content['related_documents']
        }
    
    async def _get_task_context(self, task_type: TaskType, initial_request: str) -> Dict[str, str]:
        """Определяет контекст задачи для генерации соответствующего содержимого."""
        
        if task_type == TaskType.NEW_FEATURE:
            return {
                'focus': 'проектирование нового функционала',
                'approach': 'greenfield разработка',
                'considerations': 'масштабируемость, интеграция, пользовательский опыт'
            }
        elif task_type == TaskType.MODIFY_EXISTING:
            return {
                'focus': 'модификация существующей системы',
                'approach': 'эволюционное развитие',
                'considerations': 'обратная совместимость, миграция, риски'
            }
        else:  # ANALYZE_CURRENT
            return {
                'focus': 'анализ и оптимизация текущего решения',
                'approach': 'аналитический подход',
                'considerations': 'производительность, надежность, стоимость'
            }
    
    async def _generate_title(self, session: GenerationSession, answers: Dict[str, Any]) -> str:
        """Генерирует заголовок RFC на основе задачи и ответов."""
        
        # Извлекаем ключевые слова из запроса
        request_words = session.initial_request.split()[:5]
        main_concept = ' '.join(request_words).title()
        
        if session.task_type == TaskType.NEW_FEATURE:
            return f"Архитектура {main_concept}"
        elif session.task_type == TaskType.MODIFY_EXISTING:
            return f"Модернизация {main_concept}"
        else:
            return f"Анализ и оптимизация {main_concept}"
    
    async def _extract_tags(self, session: GenerationSession, answers: Dict[str, Any]) -> List[str]:
        """Извлекает теги на основе содержимого сессии."""
        tags = [session.task_type.value]
        
        # Добавляем теги на основе ключевых слов из запроса
        request_lower = session.initial_request.lower()
        
        tech_keywords = {
            'api': 'api',
            'микросервис': 'microservices',
            'база данных': 'database',
            'безопасность': 'security',
            'производительность': 'performance',
            'уведомления': 'notifications',
            'авторизация': 'auth',
            'мониторинг': 'monitoring'
        }
        
        for keyword, tag in tech_keywords.items():
            if keyword in request_lower:
                tags.append(tag)
        
        return tags
    
    async def _generate_content_sections(
        self, 
        session: GenerationSession, 
        answers: Dict[str, Any], 
        task_context: Dict[str, str]
    ) -> Dict[str, str]:
        """Генерирует содержимое всех секций RFC с помощью LLM."""
        
        try:
            # Используем LLM для генерации улучшенного контента
            from services.llm_generation_service import LLMGenerationService
            llm_service = LLMGenerationService()
            
            # Сначала создаем базовые template vars
            template_vars = await self._create_base_template_vars(session, answers, task_context)
            
            # Затем улучшаем их с помощью LLM
            enhanced_content = await llm_service.generate_enhanced_rfc_content(session, template_vars)
            
            return enhanced_content
            
        except Exception as e:
            # Fallback на mock генерацию при ошибке LLM
            import logging
            logging.warning(f"LLM generation failed, using fallback: {e}")
            return await self._create_base_template_vars(session, answers, task_context)
    
    async def _create_base_template_vars(
        self, 
        session: GenerationSession, 
        answers: Dict[str, Any], 
        task_context: Dict[str, str]
    ) -> Dict[str, str]:
        """Создает базовые template переменные (fallback)."""
        
        return {
            'summary': f"""
Данный RFC описывает {task_context['focus']} для решения бизнес-задач, связанных с {session.initial_request}.

Предлагаемое решение основано на лучших практиках индустрии и учитывает специфические требования проекта.
""".strip(),
            
            'context': f"""
### Текущая ситуация

{session.initial_request}

### Мотивация

Необходимость {task_context['focus']} обусловлена следующими факторами:
- Бизнес-требования к {task_context['considerations']}
- Технические ограничения текущего решения
- Потребности пользователей и стейкхолдеров
""".strip(),
            
            'problem_statement': """
**Проблема:** Необходимо создать техническое решение, которое будет соответствовать бизнес-требованиям и обеспечит высокое качество пользовательского опыта.

**Критичность:** Высокая - решение напрямую влияет на ключевые метрики продукта.
""".strip(),
            
            'current_state': """
На данный момент:
- Анализ существующих решений проведен
- Выявлены ключевые требования и ограничения  
- Определены критерии успеха проекта
""".strip(),
            
            'business_goals': self._extract_business_goals(answers),
            
            'goals': """
**Основные цели:**
- Реализация функционала согласно техническим требованиям
- Обеспечение высокой производительности и надежности
- Минимизация технического долга
- Создание масштабируемого решения

**Критерии успеха:**
- Соответствие функциональным требованиям
- Прохождение всех тестов качества
- Положительная обратная связь от пользователей
""".strip(),
            
            'non_goals': """
**Не входит в область решения:**
- Полная переработка существующей архитектуры (если не требуется)
- Решение проблем, не связанных с текущей задачей
- Оптимизация компонентов, которые работают корректно
""".strip(),
            
            'architecture_overview': """
```mermaid
graph TB
    A[User Interface] --> B[API Gateway]
    B --> C[Business Logic]
    C --> D[Data Layer]
    D --> E[External Services]
```

Архитектура основана на принципах:
- **Modularity**: Четкое разделение ответственности
- **Scalability**: Горизонтальное масштабирование
- **Reliability**: Отказоустойчивость и мониторинг
- **Security**: Многоуровневая защита
""".strip(),
            
            'system_components': """
### Основные компоненты

1. **API Gateway**
   - Маршрутизация запросов
   - Аутентификация и авторизация
   - Rate limiting

2. **Business Logic Layer**
   - Обработка бизнес-логики
   - Валидация данных
   - Интеграция с внешними сервисами

3. **Data Access Layer**
   - Работа с базой данных
   - Кеширование
   - Аудит операций
""".strip(),
            
            'data_flow': """
1. Пользователь отправляет запрос через клиентское приложение
2. API Gateway валидирует запрос и маршрутизирует его
3. Business Logic обрабатывает запрос и взаимодействует с данными
4. Результат возвращается пользователю через тот же путь
""".strip(),
            
            'api_design': """
### REST API Endpoints

```yaml
paths:
  /api/v1/resource:
    get:
      summary: Получить список ресурсов
      responses:
        200:
          description: Успешный ответ
    post:
      summary: Создать новый ресурс
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Resource'
```
""".strip(),
            
            'security_considerations': """
**Безопасность данных:**
- Шифрование данных в покое и при передаче
- Аутентификация через OAuth 2.0/JWT
- Авторизация на основе ролей (RBAC)

**Защита от атак:**
- Rate limiting для предотвращения DDoS
- Валидация входных данных
- SQL injection protection
- XSS protection

**Аудит и мониторинг:**
- Логирование всех операций
- Мониторинг подозрительной активности
- Регулярные security audits
""".strip(),
            
            'performance_scalability': """
**Производительность:**
- Время отклика < 200ms для 95% запросов
- Пропускная способность > 1000 RPS
- Кеширование часто используемых данных

**Масштабируемость:**
- Horizontal scaling через контейнеризацию
- Load balancing между инстансами
- Auto-scaling на основе метрик нагрузки

**Мониторинг:**
- Real-time метрики производительности
- Alerting при превышении thresholds
- Performance profiling и optimization
""".strip(),
            
            'implementation_plan': """
Реализация разбита на 3 основные фазы с итеративной разработкой и постоянной обратной связью.
""".strip(),
            
            'phase_1_details': """
**Длительность:** 2-3 недели

**Задачи:**
- Настройка инфраструктуры и CI/CD
- Реализация базовой архитектуры
- Создание API endpoints
- Базовые unit тесты

**Результат:** MVP с основным функционалом
""".strip(),
            
            'phase_2_details': """
**Длительность:** 3-4 недели

**Задачи:**
- Добавление расширенного функционала
- Интеграция с внешними сервисами
- Performance optimization
- Integration тесты

**Результат:** Feature-complete версия
""".strip(),
            
            'phase_3_details': """
**Длительность:** 1-2 недели

**Задачи:**
- End-to-end тестирование
- Security testing
- Performance testing
- Production deployment

**Результат:** Production-ready решение
""".strip(),
            
            'tradeoffs_alternatives': """
При проектировании рассматривались различные подходы с учетом trade-offs между производительностью, сложностью и стоимостью разработки.
""".strip(),
            
            'considered_alternatives': """
1. **Монолитная архитектура**
   - Плюсы: Простота развертывания, меньше network overhead
   - Минусы: Сложность масштабирования, технологические ограничения

2. **Микросервисная архитектура**  
   - Плюсы: Независимое масштабирование, технологическое разнообразие
   - Минусы: Сложность инфраструктуры, network overhead

3. **Serverless подход**
   - Плюсы: Автоматическое масштабирование, оплата за использование
   - Минусы: Vendor lock-in, cold start latency
""".strip(),
            
            'decision_rationale': """
Выбранное решение основано на балансе между:
- Требованиями к производительности
- Сложностью разработки и поддержки
- Бюджетными ограничениями
- Временными рамками проекта
""".strip(),
            
            'systems_affected': """
**Прямое влияние:**
- API Gateway
- User Management System
- Notification Service

**Косвенное влияние:**
- Monitoring System
- Logging Infrastructure
- CI/CD Pipeline
""".strip(),
            
            'resource_requirements': """
**Development Team:**
- 2-3 Backend разработчика
- 1 Frontend разработчик  
- 1 DevOps инженер
- 0.5 QA инженера

**Infrastructure:**
- 2-3 production сервера
- Staging environment
- Development environment
- Monitoring и logging tools
""".strip(),
            
            'risk_analysis': """
**Высокие риски:**
- Интеграция с legacy системами
- Performance bottlenecks при высокой нагрузке

**Средние риски:**
- Изменения в требованиях во время разработки
- Dependency на внешние сервисы

**Митигация:**
- Extensive testing на каждом этапе
- Fallback стратегии для внешних зависимостей
- Regular stakeholder communication
""".strip(),
            
            'migration_strategy': """
**Поэтапная миграция:**
1. Parallel run с существующей системой
2. Gradual traffic switching (10% -> 50% -> 100%)
3. Monitoring и rollback plan

**Rollback план:**
- Automated rollback triggers
- Data consistency checks
- Communication plan
""".strip(),
            
            'monitoring_observability': """
**Метрики:**
- Request latency (p50, p95, p99)
- Error rate и success rate
- Throughput (RPS)
- Resource utilization (CPU, Memory)

**Alerting:**
- Error rate > 1%
- Latency p95 > 500ms
- Service availability < 99.9%

**Dashboards:**
- Real-time system health
- Business metrics
- Performance trends
""".strip(),
            
            'testing_strategy': """
**Unit Testing:**
- Code coverage > 80%
- Mocking внешних зависимостей
- Fast feedback loop

**Integration Testing:**
- API contract testing
- Database integration tests
- External service integration

**End-to-End Testing:**
- Critical user journeys
- Performance testing
- Security testing
""".strip(),
            
            'documentation_requirements': """
**Technical Documentation:**
- API documentation (OpenAPI/Swagger)
- Architecture diagrams
- Deployment guides

**User Documentation:**
- User guides
- Troubleshooting guides
- FAQ

**Operational Documentation:**
- Runbooks
- Monitoring guides
- Incident response procedures
""".strip(),
            
            'success_metrics': """
**Technical Metrics:**
- API response time < 200ms (p95)
- System availability > 99.9%
- Error rate < 0.1%

**Business Metrics:**
- User adoption rate
- Feature usage statistics
- Customer satisfaction score

**Development Metrics:**
- Code quality metrics
- Deployment frequency
- Mean time to recovery
""".strip(),
            
            'timeline': """
**Week 1-2:** Infrastructure setup, basic API
**Week 3-5:** Core functionality development
**Week 6-7:** Integration и testing
**Week 8:** Production deployment и monitoring

**Milestones:**
- [ ] Infrastructure ready (Week 2)
- [ ] MVP complete (Week 5)  
- [ ] Testing complete (Week 7)
- [ ] Production deployment (Week 8)
""".strip(),
            
            'next_steps': """
- [ ] Technical design review
- [ ] Security architecture review
- [ ] Performance requirements validation
- [ ] Resource allocation approval
- [ ] Development kickoff
""".strip(),
            
            'references': """
- [GitHub Engineering RFCs](https://github.com/github/engineering-rfcs)
- [Stripe RFC Process](https://github.com/stripe/rfcs)
- [Architecture Decision Records](https://adr.github.io/)
- [System Design Principles](https://github.com/donnemartin/system-design-primer)
""".strip(),
            
            'glossary': """
- **API Gateway**: Точка входа для всех API запросов
- **RFC**: Request for Comments - документ технического предложения
- **SLA**: Service Level Agreement - соглашение об уровне сервиса
- **RPS**: Requests Per Second - запросов в секунду
""".strip(),
            
            'related_documents': """
- System Architecture Overview
- API Design Guidelines
- Security Policy
- Deployment Procedures
""".strip()
        }
    
    def _extract_business_goals(self, answers: Dict[str, Any]) -> str:
        """Извлекает бизнес-цели из ответов пользователя."""
        
        # Ищем ответ на вопрос о бизнес-целях
        business_goal = answers.get('q1', 'Улучшение пользовательского опыта и эффективности системы')
        
        return f"""
**Основная бизнес-цель:** {business_goal}

**Дополнительные цели:**
- Повышение операционной эффективности
- Улучшение пользовательского опыта
- Снижение технических рисков
- Обеспечение масштабируемости решения
""".strip()
    
    async def _generate_fallback_rfc(self, session: GenerationSession) -> str:
        """Fallback RFC в случае ошибки с шаблоном."""
        return f"""---
rfc: FALLBACK-{uuid.uuid4().hex[:8]}
title: {session.initial_request[:50]}...
status: draft
authors: [AI Assistant]
created: {datetime.now().strftime('%Y-%m-%d')}
---

# {session.initial_request[:50]}...

## Summary

{session.initial_request}

## Implementation

Детальная реализация будет определена после технического анализа.

## Next Steps

- [ ] Техническое планирование
- [ ] Анализ требований  
- [ ] Архитектурное проектирование
"""


# Global instance
_template_service_instance = None

def get_template_service() -> TemplateServiceInterface:
    """Dependency injection для template service."""
    global _template_service_instance
    if _template_service_instance is None:
        _template_service_instance = RFCTemplateService()
    return _template_service_instance 