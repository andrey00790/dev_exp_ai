#!/usr/bin/env python3
"""
ЖИВОЙ AI EVALUATION ТЕСТ с ФИДБЕКОМ
Тестирует реальную работу AI модели и системы обучения на основе фидбека
"""

import asyncio
import httpx
import time
import json
from datetime import datetime
from typing import Dict, Any, List

class LiveAIEvaluator:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_results = []
        
    async def test_health_check(self) -> bool:
        """Проверка здоровья системы"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    async def test_ai_search_with_feedback(self, query: str, language: str = "ru") -> Dict[str, Any]:
        """Тест поиска с последующим фидбеком"""
        print(f"\n🔍 Testing search: {query} ({language})")
        
        try:
            # 1. Выполняем поиск (используем более простой endpoint)
            search_payload = {
                "query": query,
                "limit": 5,
                "language": language
            }
            
            # Пробуем разные endpoints
            search_endpoints = [
                ("/api/v1/search/search", "POST"),
                ("/api/v1/vector-search/search", "POST"), 
                ("/api/v1/vector-search/search/public", "POST"),
                ("/api/v1/search", "POST")
            ]
            
            search_result = None
            used_endpoint = None
            
            for endpoint, method in search_endpoints:
                try:
                    if method == "POST":
                        response = await self.client.post(f"{self.base_url}{endpoint}", json=search_payload)
                    else:
                        response = await self.client.get(f"{self.base_url}{endpoint}", params=search_payload)
                    
                    if response.status_code == 200:
                        search_result = response.json()
                        used_endpoint = endpoint
                        break
                    elif response.status_code not in [404, 405]:
                        print(f"   📍 {endpoint}: {response.status_code}")
                except Exception as e:
                    print(f"   ⚠️ {endpoint}: {e}")
                    continue
            
            if not search_result:
                print("   ❌ No working search endpoint found")
                return {"success": False, "error": "No search endpoint"}
            
            print(f"   ✅ Search successful via {used_endpoint}")
            results_count = len(search_result.get("results", search_result.get("documents", [])))
            print(f"   📊 Found {results_count} results")
            
            # 2. Симулируем оценку качества (в реальности - пользователь)
            quality_score = self._evaluate_search_quality(search_result, query)
            print(f"   🎯 Quality score: {quality_score:.1f}%")
            
            # 3. Отправляем фидбек
            feedback_success = await self.send_feedback(query, search_result, quality_score)
            
            return {
                "success": True,
                "endpoint": used_endpoint,
                "results_count": results_count,
                "quality_score": quality_score,
                "feedback_sent": feedback_success,
                "search_result": search_result
            }
            
        except Exception as e:
            print(f"   ❌ Search test failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _evaluate_search_quality(self, search_result: Dict, query: str) -> float:
        """Простая оценка качества поиска"""
        # Проверяем структуру результата
        if not search_result:
            return 0.0
        
        # Ищем результаты в разных полях
        results = search_result.get("results", 
                  search_result.get("documents", 
                  search_result.get("data", [])))
        
        if not results:
            return 20.0  # Базовый балл за успешный ответ
        
        # Оцениваем релевантность (упрощенно)
        query_words = set(query.lower().split())
        total_relevance = 0
        
        for result in results[:3]:  # Топ-3 результата
            title = str(result.get("title", "")).lower()
            content = str(result.get("content", result.get("text", ""))).lower()
            
            combined_text = f"{title} {content}"
            result_words = set(combined_text.split())
            
            overlap = len(query_words.intersection(result_words))
            relevance = (overlap / max(1, len(query_words))) * 100
            total_relevance += min(relevance, 100)
        
        avg_relevance = total_relevance / min(len(results), 3)
        final_score = min(100, 20 + avg_relevance)  # Базовый + релевантность
        
        return final_score
    
    async def send_feedback(self, query: str, search_result: Dict, quality_score: float) -> bool:
        """Отправка фидбека в систему обучения"""
        try:
            rating = 5 if quality_score >= 80 else 4 if quality_score >= 60 else 3 if quality_score >= 40 else 2
            
            feedback_payload = {
                "query": query,
                "search_results": search_result,
                "rating": rating,
                "quality_score": quality_score,
                "comment": f"Auto-evaluation: {quality_score:.1f}% quality",
                "feedback_type": "search_quality",
                "timestamp": datetime.now().isoformat(),
                "user_id": "evaluation_bot"
            }
            
            # Пробуем разные feedback endpoints
            feedback_endpoints = [
                "/api/v1/feedback",
                "/api/v1/ai/feedback",
                "/feedback"
            ]
            
            for endpoint in feedback_endpoints:
                try:
                    response = await self.client.post(f"{self.base_url}{endpoint}", json=feedback_payload)
                    if response.status_code == 200:
                        print(f"   📝 Feedback sent successfully to {endpoint}")
                        return True
                except Exception:
                    continue
            
            print("   ⚠️ No working feedback endpoint found")
            return False
            
        except Exception as e:
            print(f"   ❌ Feedback sending failed: {e}")
            return False
    
    async def test_feedback_driven_improvements(self) -> Dict[str, Any]:
        """Тест полного цикла улучшения на основе фидбека"""
        print("\n🔄 Testing feedback-driven improvement cycle...")
        
        # Тестовые запросы с ожидаемым качеством
        test_queries = [
            {"query": "OAuth 2.0 аутентификация", "language": "ru", "expected_min": 30},
            {"query": "микросервисы архитектура", "language": "ru", "expected_min": 25},
            {"query": "Docker контейнеризация", "language": "ru", "expected_min": 20},
            {"query": "API design patterns", "language": "en", "expected_min": 30},
            {"query": "database optimization", "language": "en", "expected_min": 25}
        ]
        
        results = []
        total_feedback_sent = 0
        
        for test_case in test_queries:
            result = await self.test_ai_search_with_feedback(
                test_case["query"], 
                test_case["language"]
            )
            
            if result["success"]:
                quality_ok = result["quality_score"] >= test_case["expected_min"]
                result["quality_meets_expectations"] = quality_ok
                
                if result["feedback_sent"]:
                    total_feedback_sent += 1
            
            results.append(result)
            
            # Небольшая пауза между запросами
            await asyncio.sleep(1)
        
        # Анализ результатов
        successful_tests = sum(1 for r in results if r["success"])
        avg_quality = sum(r.get("quality_score", 0) for r in results if r["success"]) / max(1, successful_tests)
        
        return {
            "total_queries": len(test_queries),
            "successful_tests": successful_tests,
            "feedback_sent_count": total_feedback_sent,
            "average_quality": avg_quality,
            "results": results,
            "improvement_potential": avg_quality < 60,  # Нужно ли переобучение
            "recommendation": "Model retraining recommended" if avg_quality < 60 else "Model performance acceptable"
        }
    
    async def close(self):
        """Закрытие клиента"""
        await self.client.aclose()

async def main():
    evaluator = LiveAIEvaluator()
    
    try:
        print("🚀 LIVE AI EVALUATION WITH FEEDBACK TESTING")
        print("=" * 60)
        
        # 1. Проверка здоровья
        if not await evaluator.test_health_check():
            print("❌ Backend not available, skipping tests")
            return False
        
        print("✅ Backend is healthy")
        
        # 2. Тест цикла фидбека
        feedback_results = await evaluator.test_feedback_driven_improvements()
        
        # 3. Отчет
        print(f"\n📊 FEEDBACK CYCLE TEST RESULTS:")
        print(f"   🔍 Total Queries: {feedback_results['total_queries']}")
        print(f"   ✅ Successful Tests: {feedback_results['successful_tests']}")
        print(f"   📝 Feedback Sent: {feedback_results['feedback_sent_count']}")
        print(f"   🎯 Average Quality: {feedback_results['average_quality']:.1f}%")
        print(f"   📈 Recommendation: {feedback_results['recommendation']}")
        
        # Сохранение результатов
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"live_ai_evaluation_results_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(feedback_results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Results saved to: {results_file}")
        
        return feedback_results['average_quality'] >= 50
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        return False
    finally:
        await evaluator.close()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)