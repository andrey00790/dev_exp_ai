#!/usr/bin/env python3
"""
Multilingual Semantic Search Evaluation Script
Evaluates search performance using Precision@k, MRR, cosine similarity for Russian & English
Usage: python evaluate_semantic_search.py --testset tests/semantic_search_eval.yml [--language ru/en/all]
"""

import argparse
import yaml
import json
import logging
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np

@dataclass
class EvaluationResult:
    query: str
    language: str
    expected_docs: List[str]
    retrieved_docs: List[str]
    precision_at_1: float
    precision_at_3: float
    precision_at_5: float
    mrr: float
    cosine_similarity: float
    execution_time_ms: float

@dataclass
class AggregateMetrics:
    total_queries: int
    languages: List[str]
    avg_precision_at_1: float
    avg_precision_at_3: float
    avg_precision_at_5: float
    avg_mrr: float
    avg_cosine_similarity: float
    avg_execution_time_ms: float
    role_breakdown: Dict[str, Dict[str, float]]
    language_breakdown: Dict[str, Dict[str, float]]

class SemanticSearchEvaluator:
    def __init__(self, target_language: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.target_language = target_language
        
    def load_test_dataset(self, testset_file: str) -> Dict:
        try:
            with open(testset_file, 'r', encoding='utf-8') as f:
                dataset = yaml.safe_load(f)
            
            # Filter by language if specified
            if self.target_language and self.target_language != 'all':
                filtered_dataset = {'metadata': dataset['metadata']}
                for role_name, role_data in dataset.items():
                    if role_name == 'metadata':
                        continue
                    filtered_data = [
                        case for case in role_data 
                        if case.get('language', 'en') == self.target_language
                    ]
                    if filtered_data:
                        filtered_dataset[role_name] = filtered_data
                dataset = filtered_dataset
            
            total_cases = sum(len(role_data) for role_name, role_data in dataset.items() if role_name != 'metadata')
            self.logger.info(f"Loaded {total_cases} test cases for language filter: {self.target_language or 'all'}")
            return dataset
        except Exception as e:
            self.logger.error(f"Failed to load test dataset: {e}")
            raise
    
    def calculate_precision_at_k(self, retrieved: List[str], relevant: List[str], k: int) -> float:
        if not retrieved or k == 0:
            return 0.0
        retrieved_at_k = retrieved[:k]
        relevant_retrieved = sum(1 for doc in retrieved_at_k if doc in relevant)
        return relevant_retrieved / min(k, len(retrieved_at_k))
    
    def calculate_mrr(self, retrieved: List[str], relevant: List[str]) -> float:
        for i, doc in enumerate(retrieved, 1):
            if doc in relevant:
                return 1.0 / i
        return 0.0
    
    async def evaluate_single_query(self, query: str, expected_docs: List[str], 
                                  relevance_scores: List[float], language: str) -> EvaluationResult:
        start_time = datetime.now()
        
        # Mock search results for demonstration
        # In real implementation, this would call the actual search service
        retrieved_docs = [
            "mock_doc_1.md", "mock_doc_2.md", "mock_doc_3.md",
            "mock_doc_4.md", "mock_doc_5.md"
        ]
        
        precision_at_1 = self.calculate_precision_at_k(retrieved_docs, expected_docs, 1)
        precision_at_3 = self.calculate_precision_at_k(retrieved_docs, expected_docs, 3)
        precision_at_5 = self.calculate_precision_at_k(retrieved_docs, expected_docs, 5)
        mrr = self.calculate_mrr(retrieved_docs, expected_docs)
        
        # Mock cosine similarity - in real implementation would be calculated from embeddings
        cosine_sim = np.random.uniform(0.6, 0.9)
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return EvaluationResult(
            query=query,
            language=language,
            expected_docs=expected_docs,
            retrieved_docs=retrieved_docs,
            precision_at_1=precision_at_1,
            precision_at_3=precision_at_3,
            precision_at_5=precision_at_5,
            mrr=mrr,
            cosine_similarity=cosine_sim,
            execution_time_ms=execution_time
        )
    
    async def evaluate_role_queries(self, role_name: str, role_data: List[Dict]) -> List[EvaluationResult]:
        results = []
        self.logger.info(f"Evaluating {len(role_data)} queries for role: {role_name}")
        
        for query_data in role_data:
            query = query_data['query']
            expected_docs = query_data['expected']
            relevance_scores = query_data['scores']
            language = query_data.get('language', 'en')
            
            result = await self.evaluate_single_query(query, expected_docs, relevance_scores, language)
            results.append(result)
            
            self.logger.info(f"[{language.upper()}] Query: '{query[:50]}...' | P@1: {result.precision_at_1:.3f} | "
                           f"P@3: {result.precision_at_3:.3f} | MRR: {result.mrr:.3f}")
        
        return results
    
    def calculate_aggregate_metrics(self, all_results: List[EvaluationResult], 
                                  role_results: Dict[str, List[EvaluationResult]]) -> AggregateMetrics:
        if not all_results:
            return AggregateMetrics(0, [], 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, {}, {})
        
        total_queries = len(all_results)
        languages = list(set(r.language for r in all_results))
        
        avg_precision_at_1 = np.mean([r.precision_at_1 for r in all_results])
        avg_precision_at_3 = np.mean([r.precision_at_3 for r in all_results])
        avg_precision_at_5 = np.mean([r.precision_at_5 for r in all_results])
        avg_mrr = np.mean([r.mrr for r in all_results])
        avg_cosine_similarity = np.mean([r.cosine_similarity for r in all_results])
        avg_execution_time = np.mean([r.execution_time_ms for r in all_results])
        
        # Role breakdown
        role_breakdown = {}
        for role_name, results in role_results.items():
            if results:
                role_breakdown[role_name] = {
                    "precision_at_1": np.mean([r.precision_at_1 for r in results]),
                    "precision_at_3": np.mean([r.precision_at_3 for r in results]),
                    "precision_at_5": np.mean([r.precision_at_5 for r in results]),
                    "mrr": np.mean([r.mrr for r in results]),
                    "cosine_similarity": np.mean([r.cosine_similarity for r in results]),
                    "execution_time_ms": np.mean([r.execution_time_ms for r in results]),
                    "query_count": len(results),
                    "languages": list(set(r.language for r in results))
                }
        
        # Language breakdown
        language_breakdown = {}
        for lang in languages:
            lang_results = [r for r in all_results if r.language == lang]
            if lang_results:
                language_breakdown[lang] = {
                    "precision_at_1": np.mean([r.precision_at_1 for r in lang_results]),
                    "precision_at_3": np.mean([r.precision_at_3 for r in lang_results]),
                    "precision_at_5": np.mean([r.precision_at_5 for r in lang_results]),
                    "mrr": np.mean([r.mrr for r in lang_results]),
                    "cosine_similarity": np.mean([r.cosine_similarity for r in lang_results]),
                    "execution_time_ms": np.mean([r.execution_time_ms for r in lang_results]),
                    "query_count": len(lang_results)
                }
        
        return AggregateMetrics(
            total_queries=total_queries,
            languages=languages,
            avg_precision_at_1=avg_precision_at_1,
            avg_precision_at_3=avg_precision_at_3,
            avg_precision_at_5=avg_precision_at_5,
            avg_mrr=avg_mrr,
            avg_cosine_similarity=avg_cosine_similarity,
            avg_execution_time_ms=avg_execution_time,
            role_breakdown=role_breakdown,
            language_breakdown=language_breakdown
        )
    
    async def run_evaluation(self, testset_file: str) -> AggregateMetrics:
        dataset = self.load_test_dataset(testset_file)
        
        all_results = []
        role_results = {}
        
        for role_name, role_data in dataset.items():
            if role_name == 'metadata':
                continue
                
            results = await self.evaluate_role_queries(role_name, role_data)
            role_results[role_name] = results
            all_results.extend(results)
        
        metrics = self.calculate_aggregate_metrics(all_results, role_results)
        return metrics
    
    def log_detailed_results(self, metrics: AggregateMetrics):
        self.logger.info("="*80)
        self.logger.info("MULTILINGUAL SEMANTIC SEARCH EVALUATION RESULTS")
        self.logger.info("="*80)
        self.logger.info(f"Total Queries: {metrics.total_queries}")
        self.logger.info(f"Languages: {', '.join(metrics.languages)}")
        self.logger.info(f"Precision@1: {metrics.avg_precision_at_1:.4f}")
        self.logger.info(f"Precision@3: {metrics.avg_precision_at_3:.4f}")
        self.logger.info(f"Precision@5: {metrics.avg_precision_at_5:.4f}")
        self.logger.info(f"MRR: {metrics.avg_mrr:.4f}")
        self.logger.info(f"Cosine Similarity: {metrics.avg_cosine_similarity:.4f}")
        self.logger.info(f"Avg Execution Time: {metrics.avg_execution_time_ms:.2f}ms")
        
        # Language breakdown
        if len(metrics.languages) > 1:
            self.logger.info("\nLANGUAGE BREAKDOWN:")
            for lang, lang_metrics in metrics.language_breakdown.items():
                lang_name = "Russian" if lang == "ru" else "English" if lang == "en" else lang.upper()
                self.logger.info(f"{lang_name} ({lang_metrics['query_count']} queries):")
                self.logger.info(f"  P@1: {lang_metrics['precision_at_1']:.4f}")
                self.logger.info(f"  P@3: {lang_metrics['precision_at_3']:.4f}")
                self.logger.info(f"  MRR: {lang_metrics['mrr']:.4f}")
                self.logger.info(f"  Cosine Sim: {lang_metrics['cosine_similarity']:.4f}")
        
        self.logger.info("\nROLE BREAKDOWN:")
        for role, role_metrics in metrics.role_breakdown.items():
            role_langs = "/".join(role_metrics['languages'])
            self.logger.info(f"{role} ({role_metrics['query_count']} queries, {role_langs}):")
            self.logger.info(f"  P@1: {role_metrics['precision_at_1']:.4f}")
            self.logger.info(f"  P@3: {role_metrics['precision_at_3']:.4f}")
            self.logger.info(f"  MRR: {role_metrics['mrr']:.4f}")
    
    def save_results_to_file(self, metrics: AggregateMetrics, output_file: str):
        results_data = {
            "evaluation_timestamp": datetime.now().isoformat(),
            "overall_metrics": {
                "total_queries": metrics.total_queries,
                "languages": metrics.languages,
                "precision_at_1": metrics.avg_precision_at_1,
                "precision_at_3": metrics.avg_precision_at_3,
                "precision_at_5": metrics.avg_precision_at_5,
                "mrr": metrics.avg_mrr,
                "cosine_similarity": metrics.avg_cosine_similarity,
                "avg_execution_time_ms": metrics.avg_execution_time_ms
            },
            "language_breakdown": metrics.language_breakdown,
            "role_breakdown": metrics.role_breakdown
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Results saved to: {output_file}")

async def main():
    parser = argparse.ArgumentParser(description="Evaluate multilingual semantic search performance")
    parser.add_argument("--testset", required=True, help="Path to test dataset YAML file")
    parser.add_argument("--language", choices=["ru", "en", "all"], default="all", 
                       help="Language filter: ru (Russian), en (English), or all")
    parser.add_argument("--output", default="semantic_search_results.json", help="Output file")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        evaluator = SemanticSearchEvaluator(target_language=args.language)
        logger.info(f"Starting evaluation with testset: {args.testset}")
        logger.info(f"Language filter: {args.language}")
        
        metrics = await evaluator.run_evaluation(args.testset)
        
        evaluator.log_detailed_results(metrics)
        evaluator.save_results_to_file(metrics, args.output)
        
        # Quality assessment
        precision_threshold = 0.7
        mrr_threshold = 0.6
        
        logger.info("\nQUALITY ASSESSMENT:")
        if metrics.avg_precision_at_3 >= precision_threshold:
            logger.info(f"✅ Precision@3 ({metrics.avg_precision_at_3:.3f}) meets threshold")
        else:
            logger.warning(f"❌ Precision@3 ({metrics.avg_precision_at_3:.3f}) below threshold")
        
        if metrics.avg_mrr >= mrr_threshold:
            logger.info(f"✅ MRR ({metrics.avg_mrr:.3f}) meets threshold")
        else:
            logger.warning(f"❌ MRR ({metrics.avg_mrr:.3f}) below threshold")
        
        # Language-specific thresholds
        if len(metrics.languages) > 1:
            logger.info("\nLANGUAGE-SPECIFIC ASSESSMENT:")
            for lang, lang_metrics in metrics.language_breakdown.items():
                lang_name = "Russian" if lang == "ru" else "English"
                if lang_metrics['precision_at_3'] >= precision_threshold:
                    logger.info(f"✅ {lang_name} Precision@3 ({lang_metrics['precision_at_3']:.3f}) meets threshold")
                else:
                    logger.warning(f"❌ {lang_name} Precision@3 ({lang_metrics['precision_at_3']:.3f}) below threshold")
        
        logger.info("Multilingual evaluation completed!")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
