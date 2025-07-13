"""
Monitoring domain - handles monitoring, analytics and health checks.
"""

from .health import router as health
from .realtime_monitoring import router as realtime_monitoring

__all__ = ["realtime_monitoring", "health"]
