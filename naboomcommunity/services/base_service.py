# services/base_service.py
import logging
from abc import ABC

logger = logging.getLogger(__name__)

class BaseService(ABC):
    """
    Base service class providing common functionality
    for all services in the naboomcommunity project.
    """
    
    def __init__(self):
        self.logger = logger
        
    def log_info(self, message, *args, **kwargs):
        """Log info message with service context."""
        self.logger.info(f"[{self.__class__.__name__}] {message}", *args, **kwargs)
        
    def log_error(self, message, *args, **kwargs):
        """Log error message with service context."""
        self.logger.error(f"[{self.__class__.__name__}] {message}", *args, **kwargs)
        
    def log_warning(self, message, *args, **kwargs):
        """Log warning message with service context."""
        self.logger.warning(f"[{self.__class__.__name__}] {message}", *args, **kwargs)
