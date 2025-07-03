"""
LLM module - Compatibility wrapper for adapters.llm
"""

# Re-export everything from adapters.llm for backward compatibility
from adapters.llm.llm_loader import (
    EnhancedLLMClient,
    LLMConfig,
    load_llm,
    load_llm_config,
    create_legacy_client
)

# Create LLMLoader alias for backward compatibility
LLMLoader = EnhancedLLMClient

__all__ = [
    "EnhancedLLMClient",
    "LLMConfig", 
    "LLMLoader",
    "load_llm",
    "load_llm_config",
    "create_legacy_client"
] 