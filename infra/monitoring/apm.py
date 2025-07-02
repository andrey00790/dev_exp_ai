"""
AI Assistant MVP - Application Performance Monitoring (APM)
Simplified stub for testing
"""

import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class APMManager:
    """Simplified APM Manager for testing"""
    
    def __init__(self):
        self.enabled = False
        
    def initialize(self):
        """Initialize APM (stub)"""
        pass

# Global APM manager instance
apm_manager = APMManager()

@contextmanager
def active_request_context(request_id, operation):
    """Context manager for request tracing (stub)"""
    try:
        yield
    finally:
        pass

def record_http_metrics(*args):
    """Record HTTP metrics (stub)"""
    pass 