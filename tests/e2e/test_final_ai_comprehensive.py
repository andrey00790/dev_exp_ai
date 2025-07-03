#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE AI EVALUATION WITH FEEDBACK & RETRAINING
Полный тест системы AI с фидбеком и переобучением модели
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, List

import httpx


class FinalAIEvaluator:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=120.0)

    async def test_search_with_feedback_cycle(self) -> Dict[str, Any]:
        """Полный цикл поиск -> оценка -> фидбек -> переобучение"""
        print("🚀 FINAL COMPREHENSIVE AI EVALUATION")
        print("=" * 60)

        # Тестовые запросы разного качества
        test_scenarios = [
            {
                "query": "OAuth 2.0 authentication",
                "language": "en",
                "expected_quality": "high",
            },
            {
                "query": "микросервисы архитектура",
                "language": "ru",
                "expected_quality": "medium",
            },
            {
                "query": "Docker deployment patterns",
                "language": "en",
                "expected_quality": "high",
            },
            {
                "query": "PostgreSQL оптимизация",
                "language": "ru",
                "expected_quality": "medium",
            },
            {
                "query": "React state management",
                "language": "en",
                "expected_quality": "high",
            },
        ]

        all_results = []
        total_feedback_sent = 0

        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n📝 Test {i}/5: {scenario['query']} ({scenario['language']})")

            # 1. Выполняем поиск
            search_result = await self._perform_search(scenario["query"])

            if not search_result["success"]:
                print(f"   ❌ Search failed: {search_result.get('error')}")
                continue

            # 2. Оцениваем качество
            quality_score = self._evaluate_quality(
                search_result["data"], scenario["query"]
            )
            print(f"   🎯 Quality: {quality_score:.1f}%")

            # 3. Отправляем фидбек
            feedback_result = await self._send_feedback(
                scenario["query"], search_result["data"], quality_score
            )

            if feedback_result["success"]:
                total_feedback_sent += 1
                print(f"   ✅ Feedback sent successfully")
            else:
                print(f"   ❌ Feedback failed: {feedback_result.get('error')}")

            result = {
                "scenario": scenario,
                "search_success": search_result["success"],
                "quality_score": quality_score,
                "feedback_sent": feedback_result["success"],
                "timestamp": datetime.now().isoformat(),
            }
            all_results.append(result)

            # Пауза между тестами
            await asyncio.sleep(2)

        # 4. Анализ результатов
        successful_searches = sum(1 for r in all_results if r["search_success"])
        avg_quality = sum(
            r["quality_score"] for r in all_results if r["search_success"]
        ) / max(1, successful_searches)

        # 5. Проверка необходимости переобучения
        retraining_needed = avg_quality < 60 or total_feedback_sent >= 3

        if retraining_needed:
            print(f"\n🧠 TRIGGERING MODEL RETRAINING...")
            retraining_result = await self._trigger_retraining()
        else:
            retraining_result = {"triggered": False, "reason": "Quality threshold met"}

        final_result = {
            "test_summary": {
                "total_tests": len(test_scenarios),
                "successful_searches": successful_searches,
                "feedback_sent": total_feedback_sent,
                "average_quality": avg_quality,
            },
            "individual_results": all_results,
            "retraining": retraining_result,
            "recommendation": self._generate_recommendation(
                avg_quality, total_feedback_sent
            ),
            "timestamp": datetime.now().isoformat(),
        }

        return final_result

    async def _perform_search(self, query: str) -> Dict[str, Any]:
        """Выполняет поиск"""
        try:
            payload = {
                "query": query,
                "limit": 5,
                "source_types": ["confluence", "gitlab"],
                "include_snippets": True,
            }

            response = await self.client.post(
                f"{self.base_url}/api/v1/search/search", json=payload
            )

            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _evaluate_quality(self, search_data: Dict, query: str) -> float:
        """Оценивает качество результатов поиска"""
        if not search_data:
            return 0.0

        results = search_data.get("results", [])
        if not results:
            return 10.0  # Минимальный балл за ответ

        # Базовая оценка
        base_score = 30.0

        # Оценка релевантности
        query_words = set(query.lower().split())
        total_relevance = 0

        for result in results[:3]:
            title = str(result.get("title", "")).lower()
            content = str(result.get("content", "")).lower()

            combined_text = f"{title} {content}"
            result_words = set(combined_text.split())

            overlap = len(query_words.intersection(result_words))
            relevance = (overlap / max(1, len(query_words))) * 70
            total_relevance += min(relevance, 70)

        avg_relevance = total_relevance / min(len(results), 3)
        final_score = min(100, base_score + avg_relevance)

        return final_score

    async def _send_feedback(
        self, query: str, search_data: Dict, quality_score: float
    ) -> Dict[str, Any]:
        """Отправляет фидбек"""
        try:
            rating = (
                5
                if quality_score >= 80
                else 4 if quality_score >= 60 else 3 if quality_score >= 40 else 2
            )

            feedback_payload = {
                "target_id": f"search_{hash(query) % 10000}",
                "context": "search_result",  # ВАЖНО: правильный enum!
                "feedback_type": "like" if quality_score >= 50 else "dislike",
                "rating": rating,
                "comment": f"Auto-evaluation: {quality_score:.1f}% quality for query: {query}",
                "user_id": "evaluation_bot",
            }

            response = await self.client.post(
                f"{self.base_url}/api/v1/feedback", json=feedback_payload
            )

            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _trigger_retraining(self) -> Dict[str, Any]:
        """Запускает переобучение модели"""
        try:
            retraining_payload = {
                "context": "search_result",
                "trigger_reason": "quality_threshold",
                "min_examples": 5,
            }

            response = await self.client.post(
                f"{self.base_url}/api/v1/feedback/retrain", json=retraining_payload
            )

            if response.status_code == 200:
                result = response.json()
                print(
                    f"   ✅ Retraining job started: {result.get('job_id', 'unknown')}"
                )
                return {
                    "triggered": True,
                    "job_id": result.get("job_id"),
                    "data": result,
                }
            else:
                return {"triggered": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"triggered": False, "error": str(e)}

    def _generate_recommendation(self, avg_quality: float, feedback_count: int) -> str:
        """Генерирует рекомендации"""
        if avg_quality >= 80:
            return "🏆 EXCELLENT: Model performance is outstanding"
        elif avg_quality >= 60:
            return "✅ GOOD: Model performance is acceptable"
        elif avg_quality >= 40:
            return "⚠️ FAIR: Model needs improvement, consider retraining"
        else:
            return "🚨 POOR: Critical model quality issues, retraining required"

    async def close(self):
        """Закрытие клиента"""
        await self.client.aclose()


async def main():
    evaluator = FinalAIEvaluator()

    try:
        # Проверка здоровья
        health_response = await evaluator.client.get(f"{evaluator.base_url}/health")
        if health_response.status_code != 200:
            print("❌ Backend not available")
            return False

        print("✅ Backend is healthy")

        # Запуск полного evaluation
        results = await evaluator.test_search_with_feedback_cycle()

        # Отчет
        summary = results["test_summary"]
        print(f"\n📊 FINAL RESULTS:")
        print(f"   🔍 Total Tests: {summary['total_tests']}")
        print(f"   ✅ Successful Searches: {summary['successful_searches']}")
        print(f"   📝 Feedback Sent: {summary['feedback_sent']}")
        print(f"   🎯 Average Quality: {summary['average_quality']:.1f}%")
        print(
            f"   🧠 Retraining: {'✅ Triggered' if results['retraining']['triggered'] else '❌ Not needed'}"
        )
        print(f"   📈 {results['recommendation']}")

        # Сохранение результатов
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"final_ai_evaluation_{timestamp}.json"

        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"📄 Full report saved to: {results_file}")

        return summary["average_quality"] >= 50

    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        return False
    finally:
        await evaluator.close()


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
