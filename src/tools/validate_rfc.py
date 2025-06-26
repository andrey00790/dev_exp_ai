#!/usr/bin/env python3
"""
Multilingual RFC Validation Script
Validates RFC documents for YAML header, structural completeness, markdown quality for Russian & English
Usage: python validate_rfc.py --rfc path/to/rfc.md --template tests/rfc_generation_eval.yml --case-id sd_001_ru
"""

import argparse
import yaml
import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

@dataclass
class ValidationResult:
    """Results from RFC validation"""
    file_path: str
    case_id: str
    language: str
    has_yaml_header: bool
    yaml_header_valid: bool
    required_sections_found: List[str]
    missing_sections: List[str]
    section_coverage_percent: float
    markdown_syntax_valid: bool
    markdown_errors: List[str]
    technical_depth_score: float
    overall_score: float
    passed: bool

@dataclass
class RFCTemplate:
    """RFC template with required sections"""
    case_id: str
    title: str
    language: str
    required_sections: List[str]
    complexity: str
    min_section_coverage: float = 0.9

class RFCValidator:
    """Validates RFC documents against quality criteria"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.required_yaml_fields = [
            'title', 'author', 'status', 'created', 'rfc_number'
        ]
    
    def load_rfc_template(self, template_file: str, case_id: str) -> Optional[RFCTemplate]:
        """Load specific RFC template from YAML file"""
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                templates = yaml.safe_load(f)
            
            # Search for case in all categories
            for category_name, cases in templates.items():
                if category_name == 'metadata':
                    continue
                    
                for case in cases:
                    if case['id'] == case_id:
                        return RFCTemplate(
                            case_id=case['id'],
                            title=case['title'],
                            language=case.get('language', 'en'),
                            required_sections=case['sections'],
                            complexity=case['complexity'],
                            min_section_coverage=0.9
                        )
            
            self.logger.error(f"Template for case {case_id} not found")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to load template: {e}")
            return None
    
    def extract_yaml_header(self, content: str) -> Tuple[bool, Dict, str]:
        """Extract and validate YAML header from RFC content"""
        lines = content.split('\n')
        
        # Check for YAML front matter
        if not lines[0].strip().startswith('---'):
            return False, {}, content
        
        yaml_end = -1
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                yaml_end = i
                break
        
        if yaml_end == -1:
            return False, {}, content
        
        yaml_content = '\n'.join(lines[1:yaml_end])
        markdown_content = '\n'.join(lines[yaml_end + 1:])
        
        try:
            yaml_data = yaml.safe_load(yaml_content)
            return True, yaml_data or {}, markdown_content
        except yaml.YAMLError as e:
            self.logger.warning(f"Invalid YAML header: {e}")
            return False, {}, content
    
    def validate_yaml_header(self, yaml_data: Dict, language: str) -> Tuple[bool, List[str]]:
        """Validate YAML header contains required fields"""
        errors = []
        
        for field in self.required_yaml_fields:
            if field not in yaml_data:
                errors.append(f"Missing required field: {field}")
            elif not yaml_data[field]:
                errors.append(f"Empty required field: {field}")
        
        # Validate specific field formats
        if 'status' in yaml_data:
            valid_statuses = ['draft', 'proposed', 'accepted', 'rejected', 'superseded']
            if yaml_data['status'].lower() not in valid_statuses:
                errors.append(f"Invalid status: {yaml_data['status']}")
        
        if 'created' in yaml_data:
            try:
                datetime.fromisoformat(str(yaml_data['created']))
            except ValueError:
                errors.append(f"Invalid date format for 'created': {yaml_data['created']}")
        
        # Check for language field (optional but recommended)
        if 'language' not in yaml_data:
            self.logger.info(f"Language field missing in YAML header, assuming: {language}")
        elif yaml_data['language'] != language:
            self.logger.warning(f"YAML language ({yaml_data['language']}) doesn't match template language ({language})")
        
        return len(errors) == 0, errors
    
    def extract_sections(self, markdown_content: str) -> List[str]:
        """Extract section headers from markdown content"""
        sections = []
        
        # Find markdown headers (# ## ### etc.)
        header_pattern = r'^#+\s+(.+)$'
        
        for line in markdown_content.split('\n'):
            match = re.match(header_pattern, line.strip())
            if match:
                section_title = match.group(1).strip()
                sections.append(section_title)
        
        return sections
    
    def calculate_section_coverage(self, found_sections: List[str], 
                                 required_sections: List[str], language: str) -> Tuple[float, List[str], List[str]]:
        """Calculate section coverage percentage with language-aware matching"""
        found_lower = [s.lower() for s in found_sections]
        required_lower = [s.lower() for s in required_sections]
        
        matched_sections = []
        missing_sections = []
        
        for req_section in required_sections:
            req_lower = req_section.lower()
            
            # Look for exact or partial matches
            matched = False
            for found_section in found_sections:
                found_lower_section = found_section.lower()
                
                # Check for exact match or key word inclusion
                if (req_lower == found_lower_section or 
                    req_lower in found_lower_section or 
                    any(word in found_lower_section for word in req_lower.split() if len(word) > 3)):
                    matched_sections.append(req_section)
                    matched = True
                    break
            
            if not matched:
                missing_sections.append(req_section)
        
        coverage = len(matched_sections) / len(required_sections) if required_sections else 0
        return coverage, matched_sections, missing_sections
    
    def validate_markdown_syntax(self, markdown_content: str, language: str) -> Tuple[bool, List[str]]:
        """Validate markdown syntax quality with language awareness"""
        errors = []
        
        try:
            # Basic markdown validation - would need markdown import for full validation
            # For now, doing manual checks
            
            lines = markdown_content.split('\n')
            
            # Check for headers without content
            for i, line in enumerate(lines):
                if re.match(r'^#+\s+', line):
                    # Check if header is followed by empty lines or another header
                    next_content_line = None
                    for j in range(i + 1, min(i + 5, len(lines))):
                        if lines[j].strip():
                            next_content_line = lines[j].strip()
                            break
                    
                    if not next_content_line or next_content_line.startswith('#'):
                        errors.append(f"Header at line {i+1} has no content: {line}")
            
            # Check for broken links
            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            for i, line in enumerate(lines):
                matches = re.findall(link_pattern, line)
                for link_text, link_url in matches:
                    if not link_url or link_url.startswith('http'):
                        continue  # External links are okay
                    
                    # Check internal links (basic validation)
                    if link_url.startswith('#'):
                        # Anchor link - should reference a header
                        anchor = link_url[1:].lower().replace('-', ' ')
                        headers = self.extract_sections(markdown_content)
                        header_anchors = [h.lower().replace(' ', '-') for h in headers]
                        if link_url[1:] not in header_anchors:
                            errors.append(f"Broken anchor link at line {i+1}: {link_url}")
            
            # Check for code blocks without language specification
            code_block_pattern = r'^```\s*$'
            for i, line in enumerate(lines):
                if re.match(code_block_pattern, line):
                    errors.append(f"Code block at line {i+1} missing language specification")
            
            # Language-specific checks
            if language == 'ru':
                # Check for proper Russian typography
                if '...' in markdown_content and '…' not in markdown_content:
                    self.logger.info("Recommendation: Use proper ellipsis (…) instead of three dots (...) in Russian text")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Markdown parsing error: {str(e)}")
            return False, errors
    
    def assess_technical_depth(self, markdown_content: str, complexity: str, language: str) -> float:
        """Assess technical depth of the RFC content with language-specific keywords"""
        content_lower = markdown_content.lower()
        
        # Technical indicators with weights (language-agnostic and language-specific)
        base_patterns = {
            'architecture': ['architecture', 'design pattern', 'system design', 'scalability'],
            'implementation': ['implementation', 'code', 'algorithm', 'data structure'],
            'performance': ['performance', 'latency', 'throughput', 'optimization'],
            'security': ['security', 'authentication', 'authorization', 'encryption'],
            'monitoring': ['monitoring', 'observability', 'metrics', 'logging'],
            'deployment': ['deployment', 'infrastructure', 'ci/cd', 'devops'],
            'testing': ['testing', 'validation', 'verification', 'quality assurance']
        }
        
        # Russian technical terms
        russian_patterns = {
            'architecture': ['архитектура', 'паттерн', 'проектирование', 'масштабируемость'],
            'implementation': ['реализация', 'алгоритм', 'структура данных', 'код'],
            'performance': ['производительность', 'оптимизация', 'пропускная способность'],
            'security': ['безопасность', 'аутентификация', 'авторизация', 'шифрование'],
            'monitoring': ['мониторинг', 'наблюдаемость', 'метрики', 'логирование'],
            'deployment': ['развертывание', 'инфраструктура', 'devops'],
            'testing': ['тестирование', 'валидация', 'проверка', 'качество']
        }
        
        # Choose appropriate patterns based on language
        if language == 'ru':
            technical_patterns = {**base_patterns, **russian_patterns}
        else:
            technical_patterns = base_patterns
        
        # Calculate coverage of technical topics
        total_indicators = 0
        found_indicators = 0
        
        for category, patterns in technical_patterns.items():
            total_indicators += len(patterns)
            for pattern in patterns:
                if pattern in content_lower:
                    found_indicators += 1
        
        base_score = found_indicators / total_indicators if total_indicators > 0 else 0
        
        # Adjust score based on complexity requirement
        complexity_multipliers = {
            'low': 0.7,
            'medium': 0.85,
            'high': 1.0
        }
        
        multiplier = complexity_multipliers.get(complexity.lower(), 1.0)
        
        # Content length factor (longer content generally indicates more depth)
        word_count = len(markdown_content.split())
        length_factor = min(1.0, word_count / 2000)  # Expect at least 2000 words for full score
        
        final_score = base_score * multiplier * (0.7 + 0.3 * length_factor)
        
        return min(1.0, final_score)
    
    def validate_rfc_file(self, rfc_file: str, template: RFCTemplate) -> ValidationResult:
        """Validate a single RFC file against template"""
        try:
            with open(rfc_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract YAML header
            has_yaml, yaml_data, markdown_content = self.extract_yaml_header(content)
            yaml_valid, yaml_errors = self.validate_yaml_header(yaml_data, template.language) if has_yaml else (False, ['No YAML header'])
            
            # Extract and validate sections
            found_sections = self.extract_sections(markdown_content)
            coverage, matched_sections, missing_sections = self.calculate_section_coverage(
                found_sections, template.required_sections, template.language
            )
            
            # Validate markdown syntax
            markdown_valid, markdown_errors = self.validate_markdown_syntax(markdown_content, template.language)
            
            # Assess technical depth
            technical_depth = self.assess_technical_depth(markdown_content, template.complexity, template.language)
            
            # Calculate overall score
            scores = {
                'yaml_header': 0.2 if has_yaml and yaml_valid else 0,
                'section_coverage': 0.4 * coverage,
                'markdown_quality': 0.2 if markdown_valid else 0,
                'technical_depth': 0.2 * technical_depth
            }
            
            overall_score = sum(scores.values())
            
            # Determine if RFC passes (≥90% required sections + other criteria)
            passed = (
                has_yaml and yaml_valid and
                coverage >= template.min_section_coverage and
                markdown_valid and
                technical_depth >= 0.6
            )
            
            return ValidationResult(
                file_path=rfc_file,
                case_id=template.case_id,
                language=template.language,
                has_yaml_header=has_yaml,
                yaml_header_valid=yaml_valid,
                required_sections_found=matched_sections,
                missing_sections=missing_sections,
                section_coverage_percent=coverage * 100,
                markdown_syntax_valid=markdown_valid,
                markdown_errors=markdown_errors,
                technical_depth_score=technical_depth,
                overall_score=overall_score,
                passed=passed
            )
            
        except Exception as e:
            self.logger.error(f"Failed to validate RFC {rfc_file}: {e}")
            return ValidationResult(
                file_path=rfc_file,
                case_id=template.case_id,
                language=template.language,
                has_yaml_header=False,
                yaml_header_valid=False,
                required_sections_found=[],
                missing_sections=template.required_sections,
                section_coverage_percent=0.0,
                markdown_syntax_valid=False,
                markdown_errors=[str(e)],
                technical_depth_score=0.0,
                overall_score=0.0,
                passed=False
            )
    
    def log_validation_results(self, result: ValidationResult):
        """Log detailed validation results"""
        lang_flag = "🇷🇺" if result.language == "ru" else "🇺🇸" if result.language == "en" else "🌐"
        lang_name = "Russian" if result.language == "ru" else "English" if result.language == "en" else result.language.upper()
        
        self.logger.info("="*80)
        self.logger.info(f"RFC VALIDATION: {Path(result.file_path).name} {lang_flag}")
        self.logger.info(f"Case ID: {result.case_id} | Language: {lang_name}")
        self.logger.info("="*80)
        
        # YAML Header validation
        yaml_status = "✅" if result.yaml_header_valid else "❌"
        self.logger.info(f"{yaml_status} YAML Header Present: {result.has_yaml_header}")
        self.logger.info(f"{yaml_status} YAML Header Valid: {result.yaml_header_valid}")
        
        # Section coverage
        coverage_status = "✅" if result.section_coverage_percent >= 90 else "❌"
        self.logger.info(f"{coverage_status} Section Coverage: {result.section_coverage_percent:.1f}%")
        self.logger.info(f"✅ Found Sections: {len(result.required_sections_found)}")
        if result.missing_sections:
            self.logger.warning(f"❌ Missing Sections: {', '.join(result.missing_sections)}")
        
        # Markdown quality
        md_status = "✅" if result.markdown_syntax_valid else "❌"
        self.logger.info(f"{md_status} Markdown Syntax Valid: {result.markdown_syntax_valid}")
        if result.markdown_errors:
            self.logger.warning("Markdown Errors:")
            for error in result.markdown_errors[:3]:  # Show first 3 errors
                self.logger.warning(f"  - {error}")
        
        # Technical depth
        depth_status = "✅" if result.technical_depth_score >= 0.6 else "❌"
        self.logger.info(f"{depth_status} Technical Depth Score: {result.technical_depth_score:.2f}")
        
        # Overall assessment
        overall_status = "✅" if result.passed else "❌"
        self.logger.info(f"📊 Overall Score: {result.overall_score:.2f}")
        self.logger.info(f"{overall_status} Validation Result: {'PASSED' if result.passed else 'FAILED'}")
        
        if not result.passed:
            self.logger.warning(f"❌ {lang_name} RFC validation failed. Please address the issues above.")

def main():
    """Main validation function"""
    parser = argparse.ArgumentParser(description="Validate multilingual RFC document")
    parser.add_argument("--rfc", required=True, help="Path to RFC markdown file")
    parser.add_argument("--template", required=True, help="Path to RFC template YAML file")
    parser.add_argument("--case-id", required=True, help="Template case ID (e.g., sd_001_ru, ms_002_en)")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        validator = RFCValidator()
        
        # Load template
        template = validator.load_rfc_template(args.template, args.case_id)
        if not template:
            logger.error(f"Failed to load template for case {args.case_id}")
            return 1
        
        # Validate RFC
        logger.info(f"Validating RFC: {args.rfc}")
        logger.info(f"Against template: {template.title} ({template.case_id}) - {template.language.upper()}")
        
        result = validator.validate_rfc_file(args.rfc, template)
        
        # Log results
        validator.log_validation_results(result)
        
        # Return appropriate exit code
        return 0 if result.passed else 1
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 