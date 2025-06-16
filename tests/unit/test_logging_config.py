"""
Tests for logging configuration module.
"""
import logging
import sys
from unittest.mock import patch, MagicMock
import pytest

from app.logging_config import setup_logging


class TestLoggingConfig:
    """Test logging configuration."""
    
    @patch('app.logging_config.logging.basicConfig')
    @patch('app.logging_config.logging.getLogger')
    def test_setup_logging_configures_basic_config(self, mock_get_logger, mock_basic_config):
        """Test that setup_logging configures basic logging."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        setup_logging()
        
        # Verify basicConfig was called with correct parameters
        mock_basic_config.assert_called_once_with(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            stream=sys.stdout
        )
        
        # Verify uvicorn logger propagation is disabled
        mock_get_logger.assert_called_once_with('uvicorn.error')
        assert mock_logger.propagate is False
    
    def test_setup_logging_integration(self):
        """Test setup_logging integration."""
        # Store original state
        original_handlers = logging.root.handlers[:]
        original_level = logging.root.level
        
        try:
            # Clear existing handlers
            logging.root.handlers = []
            
            # Call setup_logging
            setup_logging()
            
            # Verify logging is configured
            assert logging.root.level == logging.INFO
            assert len(logging.root.handlers) > 0
            
            # Verify uvicorn logger
            uvicorn_logger = logging.getLogger('uvicorn.error')
            assert uvicorn_logger.propagate is False
            
        finally:
            # Restore original state
            logging.root.handlers = original_handlers
            logging.root.level = original_level 