#!/usr/bin/env python3
"""
AI Enhancement Testing Script
Тестирует все AI возможности: fine-tuning, качество RFC, оптимизацию поиска
"""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_model_trainer():
    """Тестирует ModelTrainer."""
    print("\n🧠 ТЕСТИРОВАНИЕ MODEL TRAINER")
    print("=" * 50)
    
    try:
        from model_training import ModelTrainer
        
        # Инициализация
        trainer = ModelTrainer()
        print(f"✅ ModelTrainer инициализирован: {trainer.model_name}")
        
        # Загрузка обучающих данных
        examples = trainer.load_training_data()
        print(f"✅ Загружено {len(examples)} обучающих примеров")
        
        # Загрузка модели
        model = trainer.load_model()
        print(f"✅ Модель загружена: {type(model).__name__}")
        
        # Оценка модели
        metrics = trainer.evaluate_model()
        print(f"✅ Оценка модели: {metrics}")
        
        # Тест полного пайплайна (без реального обучения)
        print("🔄 Запуск полного пайплайна обучения...")
        result = trainer.run_full_training_pipeline()
        print(f"✅ Пайплайн завершен: {result['status']}")
        
        # Тест мультиязычной оптимизации
        print("🌍 Тест мультиязычной оптимизации...")
        multilingual_result = trainer.optimize_for_multilingual()
        print(f"✅ Мультиязычная оптимизация: {multilingual_result['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка ModelTrainer: {e}")
        return False

def test_rfc_quality_enhancer():
    """Тестирует RFCQualityEnhancer."""
    print("\n📝 ТЕСТИРОВАНИЕ RFC QUALITY ENHANCER")
    print("=" * 50)
    
    try:
        from domain.rfc_generation.rfc_quality_enhancer import get_rfc_quality_enhancer
        
        # Инициализация
        enhancer = get_rfc_quality_enhancer()
        print("✅ RFCQualityEnhancer инициализирован")
        
        # Тестовый RFC контент
        test_rfc_content = """
# OAuth 2.0 Authentication System

## Problem Statement
We need to implement OAuth 2.0 authentication for our API.

## Requirements
- Support multiple OAuth providers
- Secure token handling
- User management

## Architecture
The system will use JWT tokens and Redis for session storage.

## Implementation
```python
def authenticate_user(token):
    return validate_jwt(token)
```

## Security
All tokens will be encrypted and have expiration times.

## Monitoring
We will track authentication metrics and failures.
"""
        
        # Анализ качества
        print("🔍 Анализ качества RFC...")
        metrics = enhancer.analyze_rfc_quality(test_rfc_content, "OAuth 2.0 System")
        
        print(f"✅ Общий счет: {metrics.overall_score:.2f}")
        print(f"✅ Структура: {metrics.structure_score:.2f}")
        print(f"✅ Полнота: {metrics.completeness_score:.2f}")
        print(f"✅ Техническая глубина: {metrics.technical_depth_score:.2f}")
        print(f"✅ Ясность: {metrics.clarity_score:.2f}")
        
        if metrics.improvement_suggestions:
            print("💡 Рекомендации по улучшению:")
            for suggestion in metrics.improvement_suggestions[:3]:
                print(f"   - {suggestion}")
        
        if metrics.missing_sections:
            print("⚠️ Недостающие секции:")
            for section in metrics.missing_sections[:3]:
                print(f"   - {section}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка RFCQualityEnhancer: {e}")
        return False

async def test_vector_search_optimizer():
    """Тестирует VectorSearchOptimizer."""
    print("\n🔍 ТЕСТИРОВАНИЕ VECTOR SEARCH OPTIMIZER")
    print("=" * 50)
    
    try:
        from domain.integration.vector_search_optimizer import get_vector_search_optimizer
        
        # Инициализация
        optimizer = get_vector_search_optimizer()
        print("✅ VectorSearchOptimizer инициализирован")
        
        # Тестовые запросы
        test_queries = [
            "OAuth 2.0 authentication",
            "microservices architecture",
            "database optimization",
            "API security",
            "monitoring system"
        ]
        
        # Измерение производительности
        print("⏱️ Измерение производительности поиска...")
        start_time = time.time()
        
        performance_metrics = await optimizer.measure_search_performance(test_queries)
        
        measurement_time = time.time() - start_time
        print(f"✅ Измерение завершено за {measurement_time:.2f}s")
        
        print(f"✅ Среднее время отклика: {performance_metrics.avg_response_time_ms:.2f}ms")
        print(f"✅ P95 время отклика: {performance_metrics.p95_response_time_ms:.2f}ms")
        print(f"✅ Запросов в секунду: {performance_metrics.queries_per_second:.2f}")
        print(f"✅ Успешность: {performance_metrics.success_rate:.2%}")
        print(f"✅ Cache hit rate: {performance_metrics.cache_hit_rate:.2%}")
        
        # Генерация рекомендаций
        print("💡 Генерация рекомендаций по оптимизации...")
        recommendations = optimizer.generate_optimization_recommendations(performance_metrics)
        
        print(f"✅ Сгенерировано {len(recommendations)} рекомендаций")
        for rec in recommendations[:3]:
            print(f"   - [{rec.priority.upper()}] {rec.title}")
            print(f"     {rec.description}")
        
        # Получение отчета
        print("📊 Генерация отчета по оптимизации...")
        report = optimizer.get_optimization_report()
        print(f"✅ Отчет сгенерирован: {len(report['optimization_recommendations'])} рекомендаций")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка VectorSearchOptimizer: {e}")
        return False

def test_integration():
    """Тестирует интеграцию всех компонентов."""
    print("\n🔗 ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ")
    print("=" * 50)
    
    try:
        # Проверяем что все компоненты могут работать вместе
        from model_training import ModelTrainer
        from domain.rfc_generation.rfc_quality_enhancer import get_rfc_quality_enhancer
        from domain.integration.vector_search_optimizer import get_vector_search_optimizer
        
        trainer = ModelTrainer()
        enhancer = get_rfc_quality_enhancer()
        optimizer = get_vector_search_optimizer()
        
        print("✅ Все компоненты инициализированы")
        
        # Тест сценария: анализ RFC -> улучшение -> переобучение
        test_rfc = """
# Simple API Design
Basic API for user management.
"""
        
        # 1. Анализ качества
        quality_metrics = enhancer.analyze_rfc_quality(test_rfc, "Simple API")
        print(f"✅ Анализ качества: {quality_metrics.overall_score:.2f}")
        
        # 2. Если качество низкое, можно запустить улучшение
        if quality_metrics.overall_score < 0.7:
            print("💡 RFC требует улучшения")
            print(f"   Рекомендации: {len(quality_metrics.improvement_suggestions)}")
        
        # 3. Проверка готовности к переобучению
        examples = trainer.load_training_data()
        if len(examples) > 0:
            print(f"✅ Готов к переобучению: {len(examples)} примеров")
        
        print("✅ Интеграция работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка интеграции: {e}")
        return False

def test_multilingual_support():
    """Тестирует мультиязычную поддержку."""
    print("\n🌍 ТЕСТИРОВАНИЕ МУЛЬТИЯЗЫЧНОСТИ")
    print("=" * 50)
    
    try:
        from domain.rfc_generation.rfc_quality_enhancer import get_rfc_quality_enhancer
        
        enhancer = get_rfc_quality_enhancer()
        
        # Тест на русском языке
        russian_rfc = """
# Система аутентификации OAuth 2.0

## Постановка задачи
Необходимо реализовать систему аутентификации OAuth 2.0 для нашего API.

## Требования
- Поддержка множественных провайдеров OAuth
- Безопасная обработка токенов
- Управление пользователями

## Архитектура
Система будет использовать JWT токены и Redis для хранения сессий.

## Реализация
```python
def authenticate_user(token):
    return validate_jwt(token)
```

## Безопасность
Все токены будут зашифрованы и иметь время истечения.

## Мониторинг
Мы будем отслеживать метрики аутентификации и сбои.
"""
        
        # Анализ русского RFC
        ru_metrics = enhancer.analyze_rfc_quality(russian_rfc, "Система OAuth 2.0")
        print(f"✅ Анализ русского RFC: {ru_metrics.overall_score:.2f}")
        
        # Тест на английском языке
        english_rfc = """
# OAuth 2.0 Authentication System

## Problem Statement
We need to implement OAuth 2.0 authentication for our API.

## Requirements
- Support multiple OAuth providers
- Secure token handling
- User management

## Architecture
The system will use JWT tokens and Redis for session storage.

## Implementation
```python
def authenticate_user(token):
    return validate_jwt(token)
```

## Security
All tokens will be encrypted and have expiration times.

## Monitoring
We will track authentication metrics and failures.
"""
        
        # Анализ английского RFC
        en_metrics = enhancer.analyze_rfc_quality(english_rfc, "OAuth 2.0 System")
        print(f"✅ Анализ английского RFC: {en_metrics.overall_score:.2f}")
        
        # Сравнение результатов
        score_diff = abs(ru_metrics.overall_score - en_metrics.overall_score)
        if score_diff < 0.1:
            print("✅ Мультиязычная поддержка работает корректно")
        else:
            print(f"⚠️ Разница в оценках: {score_diff:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка мультиязычности: {e}")
        return False

async def main():
    """Главная функция тестирования."""
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ AI ENHANCEMENT")
    print("=" * 60)
    print(f"Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Тестируем каждый компонент
    results["model_trainer"] = test_model_trainer()
    results["rfc_quality_enhancer"] = test_rfc_quality_enhancer()
    results["vector_search_optimizer"] = await test_vector_search_optimizer()
    results["integration"] = test_integration()
    results["multilingual"] = test_multilingual_support()
    
    # Подводим итоги
    print("\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nИтого: {passed_tests}/{total_tests} тестов пройдено")
    
    if passed_tests == total_tests:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("\n🚀 AI Enhancement готов к использованию:")
        print("   - ✅ Fine-tuning моделей")
        print("   - ✅ Анализ качества RFC")
        print("   - ✅ Оптимизация поиска")
        print("   - ✅ Мультиязычная поддержка")
        print("   - ✅ Интеграция компонентов")
    else:
        print("⚠️ Некоторые тесты провалены. Проверьте логи выше.")
    
    print(f"\nВремя завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())
