#!/usr/bin/env python3
"""
AI Q&A Generation and Quality Assessment Test (Fixed)
Tests the AI system using available endpoints for question/answer generation
"""

import asyncio
import json
import time
import statistics
from typing import List, Dict, Any
import httpx
import numpy as np
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_SCENARIOS = [
    {
        "context": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints.",
        "topic": "FastAPI basics",
        "question": "What is FastAPI and what are its main features?"
    },
    {
        "context": "Docker is a platform that uses OS-level virtualization to deliver software in packages called containers.",
        "topic": "Docker containerization",
        "question": "How does Docker containerization work?"
    },
    {
        "context": "PostgreSQL is a powerful, open source object-relational database system with over 30 years of active development.",
        "topic": "PostgreSQL database",
        "question": "What makes PostgreSQL a powerful database system?"
    },
    {
        "context": "React is a JavaScript library for building user interfaces, particularly web applications with interactive UIs.",
        "topic": "React development", 
        "question": "What is React used for in web development?"
    },
    {
        "context": "Machine learning is a method of data analysis that automates analytical model building using algorithms that iteratively learn from data.",
        "topic": "Machine learning",
        "question": "How does machine learning automate data analysis?"
    }
]

class AIQualityTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_results = []
        self.quality_metrics = {
            "rfc_generation": [],
            "llm_generation": [], 
            "search_accuracy": [],
            "response_times": [],
            "overall_quality": []
        }
    
    async def test_rfc_generation(self, context: str, topic: str, question: str) -> Dict[str, Any]:
        """Test RFC generation as Q&A system"""
        print(f"\n📝 Testing RFC generation for: {topic}")
        
        start_time = time.time()
        
        payload = {
            "task_type": "analysis",
            "initial_request": f"Generate comprehensive documentation about: {topic}. Answer: {question}",
            "context": context,
            "priority": "medium"
        }
        
        try:
            # Start RFC generation
            response = await self.client.post(f"{self.base_url}/api/v1/generate", json=payload)
            
            if response.status_code == 200:
                session_data = response.json()
                session_id = session_data.get("session_id")
                questions = session_data.get("questions", [])
                
                print(f"✅ Session created: {session_id}")
                print(f"   Generated {len(questions)} clarifying questions")
                
                # Answer the questions (simulate)
                if questions:
                    answers = []
                    for i, q in enumerate(questions[:3]):  # Answer first 3 questions
                        answer = f"Answer {i+1}: Based on the context, this relates to {topic.lower()} functionality."
                        answers.append({"question_id": q.get("id", i), "answer": answer})
                    
                    answer_response = await self.client.post(
                        f"{self.base_url}/api/v1/generate/answer",
                        json={"session_id": session_id, "answers": answers}
                    )
                    
                    if answer_response.status_code == 200:
                        print(f"✅ Answered {len(answers)} questions")
                
                # Finalize RFC
                finalize_response = await self.client.post(
                    f"{self.base_url}/api/v1/generate/finalize",
                    json={"session_id": session_id}
                )
                
                response_time = time.time() - start_time
                self.quality_metrics["response_times"].append(response_time)
                
                if finalize_response.status_code == 200:
                    result = finalize_response.json()
                    rfc_content = result.get("rfc", {})
                    content = rfc_content.get("content", "")
                    
                    quality_score = self.evaluate_content_quality(content, context, question)
                    self.quality_metrics["rfc_generation"].append(quality_score)
                    
                    print(f"✅ RFC generated in {response_time:.2f}s")
                    print(f"   Content length: {len(content)} chars")
                    print(f"   Quality score: {quality_score:.1f}%")
                    
                    return {
                        "success": True,
                        "content": content,
                        "quality_score": quality_score,
                        "response_time": response_time,
                        "session_id": session_id,
                        "questions_count": len(questions)
                    }
                else:
                    print(f"❌ RFC finalization failed: {finalize_response.status_code}")
                    return {"success": False, "error": f"Finalization failed"}
            else:
                print(f"❌ RFC generation failed: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ RFC generation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_llm_generation(self, context: str, question: str) -> Dict[str, Any]:
        """Test direct LLM generation"""
        print(f"\n🤖 Testing LLM generation for: {question[:50]}...")
        
        start_time = time.time()
        
        payload = {
            "prompt": f"Context: {context}\n\nQuestion: {question}\n\nProvide a detailed answer:",
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        try:
            response = await self.client.post(f"{self.base_url}/api/v1/llm/generate", json=payload)
            
            response_time = time.time() - start_time
            self.quality_metrics["response_times"].append(response_time)
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("generated_text", "")
                
                quality_score = self.evaluate_content_quality(generated_text, context, question)
                self.quality_metrics["llm_generation"].append(quality_score)
                
                print(f"✅ LLM response in {response_time:.2f}s")
                print(f"   Response length: {len(generated_text)} chars")
                print(f"   Quality score: {quality_score:.1f}%")
                
                return {
                    "success": True,
                    "content": generated_text,
                    "quality_score": quality_score,
                    "response_time": response_time
                }
            else:
                print(f"❌ LLM generation failed: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ LLM generation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_search_functionality(self, query: str, context: str) -> Dict[str, Any]:
        """Test search functionality"""
        print(f"\n🔍 Testing search for: {query[:50]}...")
        
        start_time = time.time()
        
        payload = {
            "query": query,
            "limit": 5
        }
        
        try:
            response = await self.client.post(f"{self.base_url}/api/v1/search", json=payload)
            
            response_time = time.time() - start_time
            self.quality_metrics["response_times"].append(response_time)
            
            if response.status_code == 200:
                result = response.json()
                results = result.get("results", [])
                
                # Calculate search accuracy based on relevance
                accuracy = self.evaluate_search_accuracy(results, query, context)
                self.quality_metrics["search_accuracy"].append(accuracy)
                
                print(f"✅ Search completed in {response_time:.2f}s")
                print(f"   Found {len(results)} results")
                print(f"   Search accuracy: {accuracy:.1f}%")
                
                return {
                    "success": True,
                    "results": results,
                    "accuracy": accuracy,
                    "response_time": response_time,
                    "results_count": len(results)
                }
            else:
                print(f"❌ Search failed: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Search error: {e}")
            return {"success": False, "error": str(e)}
    
    def evaluate_content_quality(self, content: str, context: str, question: str) -> float:
        """Evaluate quality of generated content"""
        if not content or len(content.strip()) < 20:
            return 0.0
        
        score = 0.0
        
        # Length appropriateness (25 points)
        word_count = len(content.split())
        if 50 <= word_count <= 300:
            length_score = 25
        elif 20 <= word_count < 50 or 300 < word_count <= 500:
            length_score = 20
        else:
            length_score = 10
        score += length_score
        
        # Context relevance (35 points)
        context_words = set(context.lower().split())
        content_words = set(content.lower().split())
        context_overlap = len(context_words.intersection(content_words))
        context_relevance = min(35, (context_overlap / max(1, len(context_words))) * 70)
        score += context_relevance
        
        # Question relevance (40 points)
        question_words = set(question.lower().split())
        question_overlap = len(question_words.intersection(content_words))
        question_relevance = min(40, (question_overlap / max(1, len(question_words))) * 80)
        score += question_relevance
        
        return score
    
    def evaluate_search_accuracy(self, results: List[Dict], query: str, context: str) -> float:
        """Evaluate search result accuracy"""
        if not results:
            return 0.0
        
        query_words = set(query.lower().split())
        context_words = set(context.lower().split())
        total_relevance = 0
        
        for result in results:
            title = result.get("title", "").lower()
            content = result.get("content", "").lower()
            result_words = set((title + " " + content).split())
            
            # Calculate relevance to query and context
            query_overlap = len(query_words.intersection(result_words))
            context_overlap = len(context_words.intersection(result_words))
            
            relevance = (query_overlap / max(1, len(query_words))) * 0.6 + \
                       (context_overlap / max(1, len(context_words))) * 0.4
            
            total_relevance += min(1.0, relevance)
        
        return (total_relevance / len(results)) * 100
    
    async def test_feedback_system(self, target_id: str, quality_score: float) -> bool:
        """Test feedback collection system"""
        try:
            rating = 5 if quality_score > 80 else 4 if quality_score > 60 else 3
            
            payload = {
                "target_id": target_id,
                "context": "ai_testing",
                "feedback_type": "rating",
                "rating": rating,
                "comment": f"Automated test feedback. Quality score: {quality_score:.1f}%"
            }
            
            response = await self.client.post(f"{self.base_url}/api/v1/feedback", json=payload)
            return response.status_code == 200
        except Exception:
            return False
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive AI system test"""
        print("🚀 Starting Comprehensive AI System Test")
        print("=" * 60)
        
        test_start_time = time.time()
        successful_tests = 0
        total_tests = 0
        
        for scenario in TEST_SCENARIOS:
            print(f"\n📋 Testing scenario: {scenario['topic']}")
            print("-" * 50)
            
            # Test RFC generation
            rfc_result = await self.test_rfc_generation(
                scenario["context"],
                scenario["topic"],
                scenario["question"]
            )
            total_tests += 1
            if rfc_result.get("success"):
                successful_tests += 1
                await self.test_feedback_system(
                    rfc_result.get("session_id", "test"),
                    rfc_result.get("quality_score", 0)
                )
            
            # Test LLM generation
            llm_result = await self.test_llm_generation(
                scenario["context"],
                scenario["question"]
            )
            total_tests += 1
            if llm_result.get("success"):
                successful_tests += 1
            
            # Test search functionality
            search_result = await self.test_search_functionality(
                scenario["question"],
                scenario["context"]
            )
            total_tests += 1
            if search_result.get("success"):
                successful_tests += 1
            
            # Calculate overall quality for this scenario
            scenario_quality = 0
            quality_count = 0
            
            if rfc_result.get("success"):
                scenario_quality += rfc_result.get("quality_score", 0)
                quality_count += 1
            
            if llm_result.get("success"):
                scenario_quality += llm_result.get("quality_score", 0)
                quality_count += 1
                
            if search_result.get("success"):
                scenario_quality += search_result.get("accuracy", 0)
                quality_count += 1
            
            if quality_count > 0:
                avg_quality = scenario_quality / quality_count
                self.quality_metrics["overall_quality"].append(avg_quality)
            
            self.test_results.append({
                "scenario": scenario["topic"],
                "rfc_result": rfc_result,
                "llm_result": llm_result,
                "search_result": search_result,
                "timestamp": datetime.now().isoformat()
            })
        
        total_time = time.time() - test_start_time
        
        # Calculate overall metrics
        overall_metrics = self.calculate_overall_metrics()
        
        # Generate comprehensive report
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_time": total_time,
                "avg_response_time": statistics.mean(self.quality_metrics["response_times"]) if self.quality_metrics["response_times"] else 0
            },
            "quality_metrics": overall_metrics,
            "detailed_results": self.test_results,
            "model_assessment": self.assess_model_quality(overall_metrics),
            "recommendations": self.generate_recommendations(overall_metrics)
        }
        
        return report
    
    def calculate_overall_metrics(self) -> Dict[str, Any]:
        """Calculate overall quality metrics"""
        metrics = {}
        
        for metric_name, values in self.quality_metrics.items():
            if values:
                metrics[metric_name] = {
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "min": min(values),
                    "max": max(values),
                    "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                    "count": len(values)
                }
            else:
                metrics[metric_name] = {"mean": 0, "median": 0, "min": 0, "max": 0, "std_dev": 0, "count": 0}
        
        return metrics
    
    def assess_model_quality(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall model quality and need for retraining"""
        
        # Calculate weighted overall score
        rfc_score = metrics.get("rfc_generation", {}).get("mean", 0)
        llm_score = metrics.get("llm_generation", {}).get("mean", 0)
        search_score = metrics.get("search_accuracy", {}).get("mean", 0)
        overall_score = metrics.get("overall_quality", {}).get("mean", 0)
        
        # Weights: RFC (40%), LLM (35%), Search (25%)
        weighted_score = (rfc_score * 0.4 + llm_score * 0.35 + search_score * 0.25)
        
        # Determine quality level
        if weighted_score >= 85:
            quality_level = "EXCELLENT"
            retraining_needed = False
            confidence = "HIGH"
        elif weighted_score >= 70:
            quality_level = "GOOD"
            retraining_needed = False
            confidence = "MEDIUM"
        elif weighted_score >= 55:
            quality_level = "FAIR"
            retraining_needed = True
            confidence = "LOW"
        else:
            quality_level = "POOR"
            retraining_needed = True
            confidence = "VERY_LOW"
        
        return {
            "weighted_score": weighted_score,
            "quality_level": quality_level,
            "retraining_needed": retraining_needed,
            "confidence": confidence,
            "component_scores": {
                "rfc_generation": rfc_score,
                "llm_generation": llm_score,
                "search_accuracy": search_score,
                "overall_quality": overall_score
            }
        }
    
    def generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations for improvement"""
        recommendations = []
        
        rfc_mean = metrics.get("rfc_generation", {}).get("mean", 0)
        llm_mean = metrics.get("llm_generation", {}).get("mean", 0)
        search_mean = metrics.get("search_accuracy", {}).get("mean", 0)
        response_time_mean = metrics.get("response_times", {}).get("mean", 0)
        
        # RFC generation recommendations
        if rfc_mean < 60:
            recommendations.append("🔧 RFC generation quality is low. Consider improving prompt engineering and context processing.")
        elif rfc_mean < 80:
            recommendations.append("⚡ RFC generation needs improvement. Fine-tune generation parameters.")
        
        # LLM generation recommendations
        if llm_mean < 60:
            recommendations.append("🤖 LLM generation quality is low. Consider model fine-tuning or using different models.")
        elif llm_mean < 80:
            recommendations.append("📝 LLM generation could be better. Optimize prompts and temperature settings.")
        
        # Search recommendations
        if search_mean < 60:
            recommendations.append("🔍 Search accuracy is low. Improve indexing and relevance scoring.")
        elif search_mean < 80:
            recommendations.append("📊 Search results need improvement. Consider better document processing.")
        
        # Performance recommendations
        if response_time_mean > 10:
            recommendations.append("⚡ Response times are slow (>10s). Optimize model inference and caching.")
        elif response_time_mean > 5:
            recommendations.append("🚀 Response times could be faster. Consider performance optimization.")
        
        if not recommendations:
            recommendations.append("✅ All components performing well. Continue monitoring and gradual improvements.")
        
        return recommendations
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

async def main():
    """Main test execution"""
    tester = AIQualityTester(BASE_URL)
    
    try:
        # Run comprehensive test
        report = await tester.run_comprehensive_test()
        
        # Print results
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE AI SYSTEM TEST RESULTS")
        print("=" * 70)
        
        summary = report["test_summary"]
        print(f"✅ Success Rate: {summary['success_rate']:.1f}% ({summary['successful_tests']}/{summary['total_tests']})")
        print(f"⏱️  Total Time: {summary['total_time']:.2f}s")
        print(f"🚀 Avg Response Time: {summary['avg_response_time']:.2f}s")
        
        print("\n📈 QUALITY METRICS:")
        metrics = report["quality_metrics"]
        print(f"📝 RFC Generation: {metrics['rfc_generation']['mean']:.1f}% ± {metrics['rfc_generation']['std_dev']:.1f}")
        print(f"🤖 LLM Generation: {metrics['llm_generation']['mean']:.1f}% ± {metrics['llm_generation']['std_dev']:.1f}")
        print(f"🔍 Search Accuracy: {metrics['search_accuracy']['mean']:.1f}% ± {metrics['search_accuracy']['std_dev']:.1f}")
        print(f"🎯 Overall Quality: {metrics['overall_quality']['mean']:.1f}% ± {metrics['overall_quality']['std_dev']:.1f}")
        
        print("\n🎯 MODEL ASSESSMENT:")
        assessment = report["model_assessment"]
        print(f"📊 Weighted Score: {assessment['weighted_score']:.1f}%")
        print(f"🏆 Quality Level: {assessment['quality_level']}")
        print(f"🔄 Retraining Needed: {'YES' if assessment['retraining_needed'] else 'NO'}")
        print(f"📈 Confidence: {assessment['confidence']}")
        
        print("\n🔧 RECOMMENDATIONS:")
        for rec in report["recommendations"]:
            print(f"  {rec}")
        
        # Save detailed report
        with open("ai_comprehensive_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: ai_comprehensive_test_report.json")
        
        # Final assessment
        if assessment["retraining_needed"]:
            print(f"\n🚨 CONCLUSION: Model retraining recommended (score: {assessment['weighted_score']:.1f}%)")
            return False
        else:
            print(f"\n✅ CONCLUSION: Model performance satisfactory (score: {assessment['weighted_score']:.1f}%)")
            return True
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False
    finally:
        await tester.close()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 