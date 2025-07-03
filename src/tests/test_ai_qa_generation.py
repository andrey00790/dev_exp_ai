#!/usr/bin/env python3
"""
AI Q&A Generation and Quality Assessment Test
Tests the AI system's ability to generate questions and answers,
then evaluates model quality and performs retraining if needed.
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
        "expected_questions": 3
    },
    {
        "context": "Docker is a platform that uses OS-level virtualization to deliver software in packages called containers.",
        "topic": "Docker containerization", 
        "expected_questions": 3
    },
    {
        "context": "PostgreSQL is a powerful, open source object-relational database system with over 30 years of active development.",
        "topic": "PostgreSQL database",
        "expected_questions": 3
    },
    {
        "context": "React is a JavaScript library for building user interfaces, particularly web applications with interactive UIs.",
        "topic": "React development",
        "expected_questions": 3
    },
    {
        "context": "Machine learning is a method of data analysis that automates analytical model building using algorithms that iteratively learn from data.",
        "topic": "Machine learning",
        "expected_questions": 3
    }
]

class AIQualityTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
        self.quality_metrics = {
            "question_generation": [],
            "answer_generation": [],
            "relevance_scores": [],
            "response_times": [],
            "accuracy_scores": []
        }
    
    async def test_question_generation(self, context: str, topic: str, expected_count: int) -> Dict[str, Any]:
        """Test AI question generation from context"""
        print(f"\n🔍 Testing question generation for: {topic}")
        
        start_time = time.time()
        
        # Generate questions using AI enhancement endpoint
        payload = {
            "text": context,
            "enhancement_type": "question_generation",
            "parameters": {
                "num_questions": expected_count,
                "difficulty": "medium",
                "question_types": ["what", "how", "why"]
            }
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/ai-enhancement/enhance",
                json=payload
            )
            
            response_time = time.time() - start_time
            self.quality_metrics["response_times"].append(response_time)
            
            if response.status_code == 200:
                result = response.json()
                questions = result.get("enhanced_text", "").split("\n")
                questions = [q.strip() for q in questions if q.strip() and "?" in q]
                
                quality_score = self.evaluate_question_quality(questions, context, expected_count)
                self.quality_metrics["question_generation"].append(quality_score)
                
                print(f"✅ Generated {len(questions)} questions in {response_time:.2f}s")
                for i, q in enumerate(questions, 1):
                    print(f"   Q{i}: {q}")
                
                return {
                    "success": True,
                    "questions": questions,
                    "quality_score": quality_score,
                    "response_time": response_time,
                    "context": context,
                    "topic": topic
                }
            else:
                print(f"❌ Question generation failed: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Question generation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_answer_generation(self, question: str, context: str) -> Dict[str, Any]:
        """Test AI answer generation for a question"""
        print(f"\n💬 Testing answer generation for: {question[:50]}...")
        
        start_time = time.time()
        
        # Generate answer using RFC generation endpoint (adapted for Q&A)
        payload = {
            "task_type": "analysis",
            "initial_request": f"Answer this question based on the context: {question}",
            "context": context,
            "priority": "medium"
        }
        
        try:
            # Start RFC generation session
            response = await self.client.post(
                f"{self.base_url}/api/v1/generate",
                json=payload
            )
            
            if response.status_code == 200:
                session_data = response.json()
                session_id = session_data.get("session_id")
                
                # Skip questions and finalize immediately for Q&A
                finalize_response = await self.client.post(
                    f"{self.base_url}/api/v1/generate/finalize",
                    json={"session_id": session_id}
                )
                
                response_time = time.time() - start_time
                self.quality_metrics["response_times"].append(response_time)
                
                if finalize_response.status_code == 200:
                    result = finalize_response.json()
                    answer = result.get("rfc", {}).get("content", "")
                    
                    quality_score = self.evaluate_answer_quality(answer, question, context)
                    self.quality_metrics["answer_generation"].append(quality_score)
                    
                    print(f"✅ Generated answer in {response_time:.2f}s")
                    print(f"   Answer: {answer[:100]}...")
                    
                    return {
                        "success": True,
                        "answer": answer,
                        "quality_score": quality_score,
                        "response_time": response_time,
                        "question": question
                    }
                else:
                    print(f"❌ Answer finalization failed: {finalize_response.status_code}")
                    return {"success": False, "error": f"Finalization failed: {finalize_response.status_code}"}
            else:
                print(f"❌ Answer generation failed: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Answer generation error: {e}")
            return {"success": False, "error": str(e)}
    
    def evaluate_question_quality(self, questions: List[str], context: str, expected_count: int) -> float:
        """Evaluate the quality of generated questions"""
        if not questions:
            return 0.0
        
        score = 0.0
        max_score = 100.0
        
        # Count score (30 points)
        count_score = min(30, (len(questions) / expected_count) * 30)
        score += count_score
        
        # Diversity score (30 points)
        question_words = set()
        for q in questions:
            question_words.update(q.lower().split())
        diversity_score = min(30, len(question_words) / len(questions) * 10)
        score += diversity_score
        
        # Relevance score (40 points)
        context_words = set(context.lower().split())
        relevance_scores = []
        for q in questions:
            q_words = set(q.lower().split())
            overlap = len(q_words.intersection(context_words))
            relevance = min(1.0, overlap / max(1, len(q_words) * 0.3))
            relevance_scores.append(relevance)
        
        avg_relevance = statistics.mean(relevance_scores) if relevance_scores else 0
        relevance_score = avg_relevance * 40
        score += relevance_score
        
        final_score = score / max_score * 100
        self.quality_metrics["relevance_scores"].append(avg_relevance)
        
        print(f"   📊 Question Quality: {final_score:.1f}% (Count: {count_score:.1f}, Diversity: {diversity_score:.1f}, Relevance: {relevance_score:.1f})")
        return final_score
    
    def evaluate_answer_quality(self, answer: str, question: str, context: str) -> float:
        """Evaluate the quality of generated answers"""
        if not answer or len(answer.strip()) < 10:
            return 0.0
        
        score = 0.0
        max_score = 100.0
        
        # Length appropriateness (20 points)
        length_score = min(20, len(answer.split()) / 50 * 20)
        if len(answer.split()) > 200:  # Penalize overly long answers
            length_score *= 0.8
        score += length_score
        
        # Relevance to question (40 points)
        question_words = set(question.lower().split())
        answer_words = set(answer.lower().split())
        question_overlap = len(question_words.intersection(answer_words))
        question_relevance = min(1.0, question_overlap / max(1, len(question_words) * 0.5))
        score += question_relevance * 40
        
        # Relevance to context (40 points)
        context_words = set(context.lower().split())
        context_overlap = len(context_words.intersection(answer_words))
        context_relevance = min(1.0, context_overlap / max(1, len(context_words) * 0.3))
        score += context_relevance * 40
        
        final_score = score / max_score * 100
        accuracy_score = (question_relevance + context_relevance) / 2
        self.quality_metrics["accuracy_scores"].append(accuracy_score)
        
        print(f"   📊 Answer Quality: {final_score:.1f}% (Length: {length_score:.1f}, Q-Rel: {question_relevance*40:.1f}, C-Rel: {context_relevance*40:.1f})")
        return final_score
    
    async def test_feedback_collection(self, session_id: str, rating: int, comment: str) -> bool:
        """Test feedback collection for model improvement"""
        try:
            payload = {
                "target_id": session_id,
                "context": "qa_generation",
                "feedback_type": "rating",
                "rating": rating,
                "comment": comment
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/feedback",
                json=payload
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Feedback collection error: {e}")
            return False
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive Q&A generation test"""
        print("🚀 Starting Comprehensive AI Q&A Generation Test")
        print("=" * 60)
        
        test_start_time = time.time()
        successful_tests = 0
        total_tests = 0
        
        for scenario in TEST_SCENARIOS:
            print(f"\n📝 Testing scenario: {scenario['topic']}")
            print("-" * 40)
            
            # Test question generation
            question_result = await self.test_question_generation(
                scenario["context"],
                scenario["topic"], 
                scenario["expected_questions"]
            )
            
            total_tests += 1
            if question_result.get("success"):
                successful_tests += 1
                
                # Test answer generation for each question
                for question in question_result.get("questions", [])[:2]:  # Test first 2 questions
                    answer_result = await self.test_answer_generation(
                        question,
                        scenario["context"]
                    )
                    
                    total_tests += 1
                    if answer_result.get("success"):
                        successful_tests += 1
                        
                        # Simulate feedback collection
                        quality_score = answer_result.get("quality_score", 0)
                        rating = 5 if quality_score > 80 else 4 if quality_score > 60 else 3
                        await self.test_feedback_collection(
                            "test_session",
                            rating,
                            f"Generated answer quality: {quality_score:.1f}%"
                        )
            
            self.test_results.append({
                "scenario": scenario["topic"],
                "question_result": question_result,
                "timestamp": datetime.now().isoformat()
            })
        
        total_time = time.time() - test_start_time
        
        # Calculate overall metrics
        overall_metrics = self.calculate_overall_metrics()
        
        # Generate test report
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
    
    def generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations for model improvement"""
        recommendations = []
        
        # Question generation recommendations
        q_gen_mean = metrics.get("question_generation", {}).get("mean", 0)
        if q_gen_mean < 70:
            recommendations.append("🔧 Question generation quality below 70%. Consider fine-tuning question generation prompts.")
        
        # Answer generation recommendations  
        a_gen_mean = metrics.get("answer_generation", {}).get("mean", 0)
        if a_gen_mean < 70:
            recommendations.append("🔧 Answer generation quality below 70%. Consider improving context understanding.")
        
        # Response time recommendations
        avg_response_time = metrics.get("response_times", {}).get("mean", 0)
        if avg_response_time > 5:
            recommendations.append("⚡ Average response time > 5s. Consider optimizing model inference speed.")
        
        # Accuracy recommendations
        accuracy_mean = metrics.get("accuracy_scores", {}).get("mean", 0)
        if accuracy_mean < 0.8:
            recommendations.append("🎯 Accuracy below 80%. Consider retraining with more relevant data.")
        
        # Relevance recommendations
        relevance_mean = metrics.get("relevance_scores", {}).get("mean", 0)
        if relevance_mean < 0.7:
            recommendations.append("🔗 Relevance below 70%. Consider improving context processing.")
        
        if not recommendations:
            recommendations.append("✅ All metrics are within acceptable ranges. System performing well.")
        
        return recommendations
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

async def main():
    """Main test execution"""
    tester = AIQualityTester(BASE_URL)
    
    try:
        # Run comprehensive test
        report = await tester.run_comprehensive_test()
        
        # Print results
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 60)
        
        summary = report["test_summary"]
        print(f"✅ Success Rate: {summary['success_rate']:.1f}% ({summary['successful_tests']}/{summary['total_tests']})")
        print(f"⏱️  Total Time: {summary['total_time']:.2f}s")
        print(f"🚀 Avg Response Time: {summary['avg_response_time']:.2f}s")
        
        print("\n📈 QUALITY METRICS:")
        metrics = report["quality_metrics"]
        print(f"❓ Question Generation: {metrics['question_generation']['mean']:.1f}% ± {metrics['question_generation']['std_dev']:.1f}")
        print(f"💬 Answer Generation: {metrics['answer_generation']['mean']:.1f}% ± {metrics['answer_generation']['std_dev']:.1f}")
        print(f"🎯 Accuracy Score: {metrics['accuracy_scores']['mean']:.1f}% ± {metrics['accuracy_scores']['std_dev']:.1f}")
        print(f"🔗 Relevance Score: {metrics['relevance_scores']['mean']:.1f}% ± {metrics['relevance_scores']['std_dev']:.1f}")
        
        print("\n🔧 RECOMMENDATIONS:")
        for rec in report["recommendations"]:
            print(f"  {rec}")
        
        # Save detailed report
        with open("ai_qa_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: ai_qa_test_report.json")
        
        # Determine if retraining is needed
        overall_quality = (
            metrics['question_generation']['mean'] + 
            metrics['answer_generation']['mean'] + 
            metrics['accuracy_scores']['mean'] * 100
        ) / 3
        
        print(f"\n🎯 Overall AI Quality Score: {overall_quality:.1f}%")
        
        if overall_quality < 70:
            print("🚨 RECOMMENDATION: Model retraining required (quality < 70%)")
            return False
        elif overall_quality < 85:
            print("⚠️  RECOMMENDATION: Model fine-tuning suggested (quality < 85%)")
            return True
        else:
            print("✅ EXCELLENT: Model performance is satisfactory (quality ≥ 85%)")
            return True
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False
    finally:
        await tester.close()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 