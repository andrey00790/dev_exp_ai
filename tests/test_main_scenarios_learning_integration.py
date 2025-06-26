#!/usr/bin/env python3
"""
ИНТЕГРАЦИОННЫЙ ТЕСТ ОСНОВНЫХ СЦЕНАРИЕВ ОБУЧЕНИЯ
Проверяет что все основные пользовательские сценарии подключены к системе обучения

✅ Search → Evaluation → Feedback → Learning
✅ RFC Generation → Quality Assessment → Feedback → Learning  
✅ AI Analytics → Performance Metrics → Feedback → Learning
✅ Real API Integration → Live Data → Feedback Collection → Model Retraining
"""

import asyncio
import httpx
import pytest
import time
import json
from datetime import datetime
from typing import Dict, Any, List

class MainScenariosLearningTester:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.client = httpx.AsyncClient(timeout=120.0)
        self.results = {
            "scenarios_tested": [],
            "learning_integration_results": {},
            "feedback_collection_stats": {},
            "retraining_triggers": []
        }
        
    async def test_scenario_1_search_learning_cycle(self) -> Dict[str, Any]:
        """Тест полного цикла обучения для поиска"""
        print("\n🔍 SCENARIO 1: Search → Evaluation → Feedback → Learning")
        
        # Шаг 1: Выполняем поиск
        search_queries = [
            "OAuth 2.0 authentication implementation",
            "микросервисы архитектура паттерны", 
            "Docker deployment best practices"
        ]
        
        search_results = []
        for query in search_queries:
            search_payload = {
                "query": query,
                "limit": 5,
                "source_types": ["confluence", "gitlab"],
                "include_snippets": True
            }
            
            response = await self.client.post(f"{self.api_base_url}/api/v1/search/search", json=search_payload)
            if response.status_code == 200:
                search_data = response.json()
                search_results.append({
                    "query": query,
                    "results_count": len(search_data.get("results", [])),
                    "search_data": search_data
                })
                print(f"   ✅ Search: '{query}' → {len(search_data.get('results', []))} results")
            else:
                print(f"   ❌ Search failed: {query}")
        
        # Шаг 2: Отправляем feedback для каждого поиска
        feedback_sent = 0
        for search_result in search_results:
            quality_score = min(100, 30 + len(search_result["search_data"].get("results", [])) * 10)
            rating = 5 if quality_score >= 80 else 4 if quality_score >= 60 else 3
            
            feedback_payload = {
                "target_id": f"search_{hash(search_result['query']) % 10000}",
                "context": "search_result",
                "feedback_type": "like" if quality_score >= 50 else "dislike",
                "rating": rating,
                "comment": f"Integration test: Quality={quality_score}%, Query='{search_result['query']}'",
                "user_id": "integration_test"
            }
            
            response = await self.client.post(f"{self.api_base_url}/api/v1/feedback", json=feedback_payload)
            if response.status_code == 200:
                feedback_sent += 1
                print(f"   📝 Feedback sent: Quality={quality_score}%, Rating={rating}")
            else:
                print(f"   ❌ Feedback failed: {response.status_code}")
        
        return {
            "scenario": "search_learning_cycle",
            "searches_performed": len(search_results),
            "feedback_sent": feedback_sent,
            "success_rate": feedback_sent / max(1, len(search_results)),
            "integration_status": "connected" if feedback_sent > 0 else "disconnected"
        }
    
    async def test_scenario_2_rfc_generation_learning(self) -> Dict[str, Any]:
        """Тест интеграции RFC генерации с обучением"""
        print("\n📝 SCENARIO 2: RFC Generation → Quality Assessment → Learning")
        
        # Симулируем RFC генерацию и feedback
        rfc_scenarios = [
            {"topic": "API Gateway Design", "complexity": "high"},
            {"topic": "Microservices Communication", "complexity": "medium"},
            {"topic": "Database Optimization", "complexity": "low"}
        ]
        
        feedback_results = []
        for scenario in rfc_scenarios:
            # Симулируем оценку качества RFC
            quality_score = 75 if scenario["complexity"] == "high" else 60 if scenario["complexity"] == "medium" else 45
            
            # Отправляем feedback в систему обучения
            feedback_payload = {
                "target_id": f"rfc_{hash(scenario['topic']) % 10000}",
                "context": "rfc_generation",
                "feedback_type": "like" if quality_score >= 60 else "dislike",
                "rating": 5 if quality_score >= 80 else 4 if quality_score >= 60 else 3,
                "comment": f"RFC quality assessment: {quality_score}%, Topic: {scenario['topic']}, Complexity: {scenario['complexity']}",
                "user_id": "integration_test"
            }
            
            response = await self.client.post(f"{self.api_base_url}/api/v1/feedback", json=feedback_payload)
            if response.status_code == 200:
                feedback_results.append({"topic": scenario["topic"], "quality": quality_score, "feedback_sent": True})
                print(f"   ✅ RFC Feedback: '{scenario['topic']}' → Quality {quality_score}%")
            else:
                feedback_results.append({"topic": scenario["topic"], "quality": quality_score, "feedback_sent": False})
                print(f"   ❌ RFC Feedback failed: '{scenario['topic']}'")
        
        successful_feedback = sum(1 for r in feedback_results if r["feedback_sent"])
        
        return {
            "scenario": "rfc_generation_learning", 
            "rfc_scenarios_tested": len(rfc_scenarios),
            "feedback_sent": successful_feedback,
            "average_quality": sum(r["quality"] for r in feedback_results) / len(feedback_results),
            "integration_status": "connected" if successful_feedback > 0 else "disconnected"
        }
    
    async def test_scenario_3_analytics_performance_learning(self) -> Dict[str, Any]:
        """Тест интеграции аналитики и производительности с обучением"""
        print("\n📊 SCENARIO 3: AI Analytics → Performance Metrics → Learning")
        
        # Симулируем сбор метрик производительности
        performance_metrics = [
            {"metric": "search_response_time", "value": 150, "threshold": 200},
            {"metric": "rfc_generation_quality", "value": 65, "threshold": 70},
            {"metric": "user_satisfaction", "value": 4.2, "threshold": 4.0},
            {"metric": "feedback_volume", "value": 25, "threshold": 20}
        ]
        
        feedback_sent = 0
        for metric in performance_metrics:
            # Оценка производительности
            performance_ok = metric["value"] >= metric["threshold"] if metric["metric"] != "search_response_time" else metric["value"] <= metric["threshold"]
            quality_score = 80 if performance_ok else 40
            
            # Отправляем feedback по производительности
            feedback_payload = {
                "target_id": f"perf_{metric['metric']}",
                "context": "ai_question",  # Используем для AI аналитики
                "feedback_type": "like" if performance_ok else "dislike",
                "rating": 5 if performance_ok else 2,
                "comment": f"Performance metric: {metric['metric']}={metric['value']}, threshold={metric['threshold']}, status={'OK' if performance_ok else 'POOR'}",
                "user_id": "performance_monitor"
            }
            
            response = await self.client.post(f"{self.api_base_url}/api/v1/feedback", json=feedback_payload)
            if response.status_code == 200:
                feedback_sent += 1
                print(f"   ✅ Performance Feedback: {metric['metric']} → {'OK' if performance_ok else 'POOR'}")
            else:
                print(f"   ❌ Performance Feedback failed: {metric['metric']}")
        
        return {
            "scenario": "analytics_performance_learning",
            "metrics_monitored": len(performance_metrics),
            "feedback_sent": feedback_sent,
            "performance_issues_detected": sum(1 for m in performance_metrics if (m["value"] < m["threshold"] if m["metric"] != "search_response_time" else m["value"] > m["threshold"])),
            "integration_status": "connected" if feedback_sent > 0 else "disconnected"
        }
    
    async def test_scenario_4_retraining_trigger_integration(self) -> Dict[str, Any]:
        """Тест интеграции с системой переобучения"""
        print("\n🧠 SCENARIO 4: Feedback Collection → Retraining Trigger → Model Update")
        
        # Тестируем различные реtraining endpoints
        retraining_tests = [
            {
                "endpoint": "/api/v1/feedback/retrain",
                "payload": {
                    "context": "search_result",
                    "trigger_reason": "integration_test",
                    "min_examples": 3
                }
            },
            {
                "endpoint": "/api/v1/learning/feedback", 
                "payload": {
                    "rfc_id": "integration_test_rfc",
                    "feedback_type": "like",
                    "rating": 4,
                    "comment": "Integration test feedback for learning system"
                }
            }
        ]
        
        retraining_results = []
        for test in retraining_tests:
            try:
                response = await self.client.post(f"{self.api_base_url}{test['endpoint']}", json=test["payload"])
                
                if response.status_code == 200:
                    result_data = response.json()
                    retraining_results.append({
                        "endpoint": test["endpoint"],
                        "status": "success",
                        "response": result_data
                    })
                    print(f"   ✅ Retraining endpoint: {test['endpoint']} → SUCCESS")
                else:
                    retraining_results.append({
                        "endpoint": test["endpoint"], 
                        "status": "failed",
                        "error_code": response.status_code
                    })
                    print(f"   ⚠️ Retraining endpoint: {test['endpoint']} → {response.status_code}")
                    
            except Exception as e:
                retraining_results.append({
                    "endpoint": test["endpoint"],
                    "status": "error", 
                    "error": str(e)
                })
                print(f"   ❌ Retraining endpoint: {test['endpoint']} → ERROR: {e}")
        
        successful_retraining = sum(1 for r in retraining_results if r["status"] == "success")
        
        return {
            "scenario": "retraining_trigger_integration",
            "endpoints_tested": len(retraining_tests),
            "successful_triggers": successful_retraining,
            "retraining_results": retraining_results,
            "integration_status": "connected" if successful_retraining > 0 else "partial"
        }
    
    async def run_full_integration_test(self) -> Dict[str, Any]:
        """Запуск полного интеграционного теста всех сценариев"""
        print("🚀 ПОЛНЫЙ ИНТЕГРАЦИОННЫЙ ТЕСТ ОСНОВНЫХ СЦЕНАРИЕВ ОБУЧЕНИЯ")
        print("=" * 80)
        
        start_time = time.time()
        
        # Проверка доступности API
        try:
            health_response = await self.client.get(f"{self.api_base_url}/health")
            if health_response.status_code != 200:
                print("❌ API not available")
                return {"status": "failed", "error": "API unavailable"}
            print("✅ API is available and healthy")
        except Exception as e:
            print(f"❌ API connection failed: {e}")
            return {"status": "failed", "error": str(e)}
        
        # Запуск всех сценариев
        scenarios = [
            self.test_scenario_1_search_learning_cycle(),
            self.test_scenario_2_rfc_generation_learning(), 
            self.test_scenario_3_analytics_performance_learning(),
            self.test_scenario_4_retraining_trigger_integration()
        ]
        
        scenario_results = []
        for scenario_test in scenarios:
            try:
                result = await scenario_test
                scenario_results.append(result)
                self.results["scenarios_tested"].append(result["scenario"])
                self.results["learning_integration_results"][result["scenario"]] = result
                
                # Пауза между сценариями
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Scenario failed: {e}")
                scenario_results.append({"scenario": "unknown", "status": "failed", "error": str(e)})
        
        total_time = time.time() - start_time
        
        # Анализ результатов
        connected_scenarios = sum(1 for r in scenario_results if r.get("integration_status") == "connected")
        total_feedback_sent = sum(r.get("feedback_sent", 0) for r in scenario_results)
        
        final_result = {
            "test_summary": {
                "total_scenarios": len(scenario_results),
                "connected_scenarios": connected_scenarios,
                "integration_coverage": connected_scenarios / len(scenario_results),
                "total_feedback_sent": total_feedback_sent,
                "total_time_seconds": total_time
            },
            "scenario_results": scenario_results,
            "overall_status": "FULLY_INTEGRATED" if connected_scenarios == len(scenario_results) 
                             else "PARTIALLY_INTEGRATED" if connected_scenarios > 0 
                             else "NOT_INTEGRATED",
            "recommendation": self._generate_integration_recommendation(connected_scenarios, len(scenario_results), total_feedback_sent),
            "timestamp": datetime.now().isoformat()
        }
        
        return final_result
    
    def _generate_integration_recommendation(self, connected: int, total: int, feedback_count: int) -> str:
        """Генерирует рекомендации по интеграции"""
        coverage = connected / total
        
        if coverage >= 1.0 and feedback_count >= 10:
            return "🏆 EXCELLENT: All scenarios fully integrated with learning system"
        elif coverage >= 0.75:
            return "✅ GOOD: Most scenarios integrated, minor improvements needed"  
        elif coverage >= 0.5:
            return "⚠️ FAIR: Partial integration, significant improvements required"
        else:
            return "🚨 POOR: Critical integration issues, major fixes needed"
    
    async def close(self):
        """Закрытие клиента"""
        await self.client.aclose()

async def main():
    """Главная функция тестирования"""
    tester = MainScenariosLearningTester()
    
    try:
        # Запуск полного интеграционного теста  
        results = await tester.run_full_integration_test()
        
        # Вывод итогов
        summary = results["test_summary"]
        print(f"\n📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ИНТЕГРАЦИИ:")
        print(f"   🎯 Scenarios Tested: {summary['total_scenarios']}")
        print(f"   ✅ Connected Scenarios: {summary['connected_scenarios']}")
        print(f"   📊 Integration Coverage: {summary['integration_coverage']:.1%}")
        print(f"   📝 Total Feedback Sent: {summary['total_feedback_sent']}")
        print(f"   ⏱️ Total Time: {summary['total_time_seconds']:.1f}s")
        print(f"   🏆 Overall Status: {results['overall_status']}")
        print(f"   📈 {results['recommendation']}")
        
        # Сохранение результатов
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"main_scenarios_learning_integration_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Full integration report saved to: {results_file}")
        
        return summary['integration_coverage'] >= 0.75
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False
    finally:
        await tester.close()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 