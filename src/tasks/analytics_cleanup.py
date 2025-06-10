"""
Scheduled task to clean up old analytics data.
"""
import logging
import os
import sys
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.knowledge.database import DatabaseManager
from src.config_unified import settings

logger = logging.getLogger(__name__)


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join('logs', 'analytics_cleanup.log'))
        ]
    )


def cleanup_analytics_data():
    """
    Clean up old analytics data based on retention settings.
    """
    try:
        logger.info("Starting analytics data cleanup")
        
        # Use unified configuration
        # Get retention periods from environment or defaults
        detailed_events_days = getattr(settings, 'analytics_detailed_retention_days', 90)
        aggregated_stats_days = getattr(settings, 'analytics_aggregated_retention_days', 365)
        
        # Initialize database manager with unified config
        db_manager = DatabaseManager({
            'database_uri': settings.database_uri,
            'postgres_host': settings.postgres_host,
            'postgres_port': settings.postgres_port,
            'postgres_db': settings.postgres_db,
            'postgres_user': settings.postgres_user,
            'postgres_password': settings.postgres_password.get_secret_value()
        })
        
        # Delete old detailed events
        logger.info(f"Deleting detailed events older than {detailed_events_days} days")
        deleted_count = db_manager.delete_old_analytics_events(days=detailed_events_days)
        logger.info(f"Deleted {deleted_count} old events")
        
        # Aggregated stats cleanup can be implemented when aggregation functionality is added
        
        logger.info("Analytics data cleanup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during analytics data cleanup: {str(e)}")
        return False


if __name__ == '__main__':
    # Set up logging
    setup_logging()
    
    # Run cleanup
    cleanup_analytics_data() 