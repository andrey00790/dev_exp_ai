"""
📊 Team Performance Forecasting Engine Demo - Phase 4B.4

Демонстрация возможностей системы прогнозирования производительности команды.
"""

import asyncio
import time
import logging
import sys
import os
from datetime import datetime, timedelta

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Основная демонстрация Team Performance Forecasting Engine"""
    
    print("\n" + "="*80)
    print("📊 TEAM PERFORMANCE FORECASTING ENGINE DEMO - PHASE 4B.4")
    print("="*80)
    
    try:
        # Импорт движка
        from domain.code_optimization.team_performance_forecasting_engine import (
            get_team_performance_forecasting_engine,
            PerformanceMetric,
            TeamMember,
            TeamMetricType
        )
        
        # Получение экземпляра движка
        engine = await get_team_performance_forecasting_engine()
        print(f"✅ Team Performance Forecasting Engine инициализирован")
        
        # Демонстрационные сценарии
        await demo_basic_team_analysis(engine, PerformanceMetric, TeamMember, TeamMetricType)
        await demo_quick_assessments(engine)
        await demo_performance_trends(engine, PerformanceMetric, TeamMetricType)
        
        # Финальные метрики
        await show_final_metrics(engine)
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Убедитесь, что Team Performance Forecasting Engine установлен правильно")
    except Exception as e:
        print(f"❌ Ошибка выполнения демо: {e}")
        logger.error(f"Ошибка демонстрации: {e}", exc_info=True)

async def demo_basic_team_analysis(engine, PerformanceMetric, TeamMember, TeamMetricType):
    """Демонстрация базового анализа команды"""
    print("\n" + "-"*60)
    print("📊 БАЗОВЫЙ АНАЛИЗ КОМАНДЫ")
    print("-"*60)
    
    # Создание примера команды
    team_members = [
        TeamMember(
            name="Alice Johnson",
            role="Tech Lead",
            experience_level="senior",
            performance_score=9.0,
            availability=1.0
        ),
        TeamMember(
            name="Bob Smith",
            role="Senior Developer",
            experience_level="senior", 
            performance_score=8.5,
            availability=0.9
        ),
        TeamMember(
            name="Carol Williams",
            role="QA Engineer",
            experience_level="middle",
            performance_score=7.5,
            availability=1.0
        )
    ]
    
    # Простые метрики команды
    basic_velocity_data = [
        PerformanceMetric(
            metric_type=TeamMetricType.VELOCITY,
            value=45.0,
            timestamp=datetime.now() - timedelta(days=21)
        ),
        PerformanceMetric(
            metric_type=TeamMetricType.VELOCITY,
            value=52.0,
            timestamp=datetime.now() - timedelta(days=14)
        ),
        PerformanceMetric(
            metric_type=TeamMetricType.VELOCITY,
            value=58.0,
            timestamp=datetime.now() - timedelta(days=7)
        )
    ]
    
    historical_metrics = {'velocity': basic_velocity_data}
    
    print("🔍 Анализируем команду из 3 разработчиков...")
    
    start_time = time.time()
    report = await engine.analyze_team_performance("demo-team-1", historical_metrics, team_members)
    analysis_time = time.time() - start_time
    
    print(f"✅ Анализ завершен за {analysis_time:.3f}s")
    print(f"📋 Результаты анализа:")
    print(f"   • Текущая производительность: {report.current_performance_score:.1f}/10")
    print(f"   • Тренд: {report.performance_trend.value.upper()}")
    print(f"   • Прогнозов сгенерировано: {len(report.forecasts)}")
    
    # Показываем ключевые метрики
    print(f"\n📊 Ключевые метрики команды:")
    for metric_name, metric_value in report.team_metrics.items():
        print(f"   • {metric_name.replace('_', ' ').title()}: {metric_value:.2f}")
    
    # Показываем прогнозы
    if report.forecasts:
        print(f"\n🔮 Краткосрочные прогнозы:")
        for forecast in report.forecasts[:2]:
            print(f"   📅 {forecast.forecast_period_days} дней:")
            print(f"      └─ Скорость: {forecast.predicted_velocity:.1f}")
            print(f"      └─ Качество: {forecast.predicted_quality_score:.1f}")
            print(f"      └─ Уверенность: {forecast.confidence_level.value.upper()}")
            print(f"      └─ Риск: {forecast.risk_level.value.upper()}")

async def demo_quick_assessments(engine):
    """Демонстрация быстрых оценок команд"""
    print("\n" + "-"*60)
    print("⚡ БЫСТРЫЕ ОЦЕНКИ КОМАНД")
    print("-"*60)
    
    teams_for_assessment = [
        {
            'id': 'high-performance-team',
            'name': 'Высокопроизводительная команда',
            'metrics': {'velocity': 85.0, 'quality_score': 9.2}
        },
        {
            'id': 'average-team',
            'name': 'Средняя команда',
            'metrics': {'velocity': 55.0, 'quality_score': 7.0}
        },
        {
            'id': 'struggling-team',
            'name': 'Команда с проблемами',
            'metrics': {'velocity': 25.0, 'quality_score': 5.5}
        }
    ]
    
    print("🔍 Проводим быстрые оценки различных команд:")
    
    for team_info in teams_for_assessment:
        print(f"\n📊 {team_info['name']}:")
        
        start_time = time.time()
        result = await engine.quick_team_assessment(team_info['id'], team_info['metrics'])
        assessment_time = time.time() - start_time
        
        print(f"   ⏱️  Время оценки: {assessment_time:.4f}s")
        print(f"   📈 Производительность: {result['performance_score']}/10")
        print(f"   🚨 Уровень риска: {result['risk_level'].upper()}")
        
        # Цветовая индикация риска
        risk_emoji = {
            'minimal': '��',
            'low': '🟡', 
            'medium': '🟠',
            'high': '🔴',
            'critical': '🚨'
        }
        print(f"   {risk_emoji.get(result['risk_level'], '❓')} Статус: {'Отлично' if result['risk_level'] in ['minimal', 'low'] else 'Требует внимания'}")

async def demo_performance_trends(engine, PerformanceMetric, TeamMetricType):
    """Демонстрация анализа трендов производительности"""
    print("\n" + "-"*60)
    print("📈 АНАЛИЗ ТРЕНДОВ ПРОИЗВОДИТЕЛЬНОСТИ")
    print("-"*60)
    
    trend_scenarios = [
        {
            'name': 'Улучшающаяся команда',
            'pattern': 'improving',
            'velocities': [30, 35, 42, 48, 55, 62]
        },
        {
            'name': 'Стабильная команда',
            'pattern': 'stable',
            'velocities': [50, 52, 48, 51, 49, 53]
        },
        {
            'name': 'Ухудшающаяся команда',
            'pattern': 'declining',
            'velocities': [65, 60, 55, 48, 42, 38]
        }
    ]
    
    print("🔍 Анализируем различные паттерны производительности:")
    
    for scenario in trend_scenarios:
        print(f"\n📊 {scenario['name']}:")
        
        # Создание данных скорости
        base_time = datetime.now()
        velocity_data = []
        for i, velocity in enumerate(scenario['velocities']):
            velocity_data.append(PerformanceMetric(
                metric_type=TeamMetricType.VELOCITY,
                value=velocity,
                timestamp=base_time - timedelta(days=(len(scenario['velocities'])-i-1)*7)
            ))
        
        historical_metrics = {'velocity': velocity_data}
        
        # Анализ
        report = await engine.analyze_team_performance(f"trend-{scenario['pattern']}", historical_metrics, [])
        
        print(f"   📈 Обнаруженный тренд: {report.performance_trend.value.upper()}")
        print(f"   📊 Производительность: {report.current_performance_score:.1f}/10")
        print(f"   📏 Средняя скорость: {report.team_metrics.get('average_velocity', 0):.1f}")
        print(f"   🎯 Стабильность: {report.team_metrics.get('velocity_stability', 0):.2f}")
        
        # Показываем краткосрочный прогноз
        if report.forecasts:
            short_term_forecast = report.forecasts[0]
            print(f"   🔮 Прогноз: {short_term_forecast.predicted_velocity:.1f} (риск: {short_term_forecast.risk_level.value})")

async def show_final_metrics(engine):
    """Показ финальных метрик движка"""
    print("\n" + "="*60)
    print("📊 ФИНАЛЬНЫЕ МЕТРИКИ ДВИЖКА")
    print("="*60)
    
    metrics = engine.get_forecasting_metrics()
    
    print(f"🔧 Статус движка: {metrics['engine_status']}")
    print(f"📈 Статистика работы:")
    print(f"   • Команд проанализировано: {metrics['metrics']['teams_analyzed']}")
    print(f"   • Прогнозов сгенерировано: {metrics['metrics']['forecasts_generated']}")
    print(f"   • Рекомендаций выдано: {metrics['metrics']['total_recommendations']}")
    print(f"   • Средняя точность прогнозов: {metrics['metrics']['average_forecast_accuracy']:.1%}")
    
    print(f"\n🎯 Возможности движка:")
    capabilities = [
        "✅ Анализ трендов скорости разработки",
        "✅ Прогнозирование производительности команды",
        "✅ Оценка рисков и их факторов",
        "✅ Анализ состава команды",
        "✅ Генерация рекомендаций по улучшению",
        "✅ Быстрые оценки команд"
    ]
    for capability in capabilities:
        print(f"   {capability}")
    
    print(f"\n🚀 Производительность:")
    print(f"   • Быстрая оценка: <0.1s")
    print(f"   • Полный анализ: <1s для команды")
    print(f"   • Поддержка параллельных запросов")
    
    print(f"\n" + "="*60)
    print("🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
    print("✨ Team Performance Forecasting Engine готов к работе!")
    print("📊 Phase 4B.4 - Team Performance Forecasting реализован!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
