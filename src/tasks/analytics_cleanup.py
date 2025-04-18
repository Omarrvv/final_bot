"""
Scheduled task to clean up old analytics data.
"""
import logging
import os
import sys
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.database_manager import DatabaseManager
from src.config import load_config

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
        
        # Load configuration
        config = load_config()
        analytics_config = config.get('ANALYTICS', {})
        retention_config = analytics_config.get('data_retention', {})
        
        # Get retention periods
        detailed_events_days = retention_config.get('detailed_events_days', 90)
        aggregated_stats_days = retention_config.get('aggregated_stats_days', 365)
        
        # Initialize database manager
        db_config = config.get('DATABASE', {})
        db_manager = DatabaseManager(db_config)
        
        # Delete old detailed events
        logger.info(f"Deleting detailed events older than {detailed_events_days} days")
        deleted_count = db_manager.delete_old_analytics_events(days=detailed_events_days)
        logger.info(f"Deleted {deleted_count} old events")
        
        # TODO: Implement aggregated stats cleanup when aggregation is implemented
        
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