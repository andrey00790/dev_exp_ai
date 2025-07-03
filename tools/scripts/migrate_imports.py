#!/usr/bin/env python3
"""
Import Migration Script - Context7 Pattern Implementation

Automatically migrates old services.* imports to new domain.* structure.
Follows Context7 best practices for safe refactoring.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Context7 pattern: Explicit mapping configuration
IMPORT_MIGRATIONS = {
    # AI Analysis Domain
    'services.ai_agent_orchestrator': 'domain.ai_analysis.ai_agent_orchestrator',
    'services.ai_code_analyzer': 'domain.ai_analysis.ai_code_analyzer', 
    'services.smart_refactoring_engine': 'domain.ai_analysis.smart_refactoring_engine',
    
    # RFC Generation Domain
    'services.rfc_generator_service': 'domain.rfc_generation.rfc_generator_service',
    'services.rfc_analyzer': 'domain.rfc_generation.rfc_analyzer',
    'services.rfc_architecture_analyzer': 'domain.rfc_generation.rfc_architecture_analyzer',
    'services.rfc_quality_enhancer': 'domain.rfc_generation.rfc_quality_enhancer',
    
    # Code Optimization Domain
    'services.ai_performance_optimizer': 'domain.code_optimization.ai_performance_optimizer',
    'services.performance_optimization_engine': 'domain.code_optimization.performance_optimization_engine',
    'services.team_performance_forecasting_engine': 'domain.code_optimization.team_performance_forecasting_engine',
    
    # Core Domain
    'services.core_logic_engine': 'domain.core.core_logic_engine',
    'services.enhanced_async_engine': 'domain.core.enhanced_async_engine',
    'services.deep_research_engine': 'domain.core.deep_research_engine',
    'services.generation_service': 'domain.core.generation_service',
    'services.llm_generation_service': 'domain.core.llm_generation_service',
    'services.learning_pipeline_service': 'domain.core.learning_pipeline_service',
    'services.predictive_analytics_engine': 'domain.core.predictive_analytics_engine',
    'services.mermaid_diagram_generator': 'domain.core.mermaid_diagram_generator',
    'services.template_service': 'domain.core.template_service',
    
    # Integration Domain
    'services.enhanced_vector_search_service': 'domain.integration.enhanced_vector_search_service',
    'services.vector_search_service': 'domain.integration.vector_search_service',
    'services.vector_search_optimizer': 'domain.integration.vector_search_optimizer',
    'services.document_service': 'domain.integration.document_service',
    'services.documentation_service': 'domain.integration.documentation_service',
    'services.data_source_service': 'domain.integration.data_source_service',
    'services.data_sync_service': 'domain.integration.data_sync_service',
    'services.search_service': 'domain.integration.search_service',
    'services.search_interface': 'domain.integration.search_interface',
    'services.search_models': 'domain.integration.search_models',
    'services.document_graph_builder': 'domain.integration.document_graph_builder',
    'services.smart_repository_integration': 'domain.integration.smart_repository_integration',
    'services.dynamic_reranker': 'domain.integration.dynamic_reranker',
    
    # Monitoring Domain
    'services.advanced_security_engine': 'domain.monitoring.advanced_security_engine',
    'services.feedback_service': 'domain.monitoring.feedback_service',
    'services.enhanced_feedback_service': 'domain.monitoring.enhanced_feedback_service',
    'services.bug_hotspot_detection_engine': 'domain.monitoring.bug_hotspot_detection_engine',
}

class ImportMigrator:
    """Context7 pattern: Safe import migration with validation"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.migrations_applied = 0
        self.files_processed = 0
        self.errors = []
    
    def migrate_file(self, file_path: Path) -> bool:
        """Migrate imports in a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Context7 pattern: Multiple migration patterns
            for old_import, new_import in IMPORT_MIGRATIONS.items():
                # Pattern 1: from services.module import ...
                pattern1 = rf'from\s+{re.escape(old_import)}\s+import'
                replacement1 = f'from {new_import} import'
                content = re.sub(pattern1, replacement1, content)
                
                # Pattern 2: import services.module
                pattern2 = rf'import\s+{re.escape(old_import)}'
                replacement2 = f'import {new_import}'
                content = re.sub(pattern2, replacement2, content)
                
                # Pattern 3: services.module.function()
                pattern3 = rf'{re.escape(old_import)}\.'
                replacement3 = f'{new_import}.'
                content = re.sub(pattern3, replacement3, content)
            
            if content != original_content:
                if not self.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                print(f"✅ {'[DRY RUN] ' if self.dry_run else ''}Migrated: {file_path}")
                self.migrations_applied += 1
                return True
            
            return False
            
        except Exception as e:
            self.errors.append(f"Error processing {file_path}: {e}")
            return False
    
    def migrate_directory(self, directory: Path, patterns: List[str] = ["*.py"]) -> None:
        """Migrate all Python files in directory"""
        
        for pattern in patterns:
            for file_path in directory.rglob(pattern):
                # Skip __pycache__ and .git directories
                if '__pycache__' in str(file_path) or '.git' in str(file_path):
                    continue
                
                self.files_processed += 1
                self.migrate_file(file_path)
    
    def print_summary(self) -> None:
        """Print migration summary"""
        print(f"\n📊 Migration Summary:")
        print(f"Files processed: {self.files_processed}")
        print(f"Migrations applied: {self.migrations_applied}")
        
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.dry_run:
            print(f"\n💡 This was a DRY RUN. Use --apply to actually migrate files.")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate services imports to domain structure')
    parser.add_argument('--apply', action='store_true', help='Actually apply migrations (default: dry run)')
    parser.add_argument('--directory', default='.', help='Directory to migrate (default: current)')
    
    args = parser.parse_args()
    
    print(f"🔄 Starting import migration {'(DRY RUN)' if not args.apply else '(APPLYING CHANGES)'}")
    
    migrator = ImportMigrator(dry_run=not args.apply)
    migrator.migrate_directory(Path(args.directory))
    migrator.print_summary()

if __name__ == "__main__":
    main() 