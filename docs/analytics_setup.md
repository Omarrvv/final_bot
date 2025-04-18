# Analytics System Setup

This document provides instructions for setting up and configuring the analytics system for the Egypt Tourism Chatbot.

## Overview

The analytics system tracks user interactions with the chatbot and provides insights through a dashboard. It includes:

- Event tracking (messages, intents, entities, feedback)
- Data storage in MongoDB
- Analytics API endpoints
- Admin dashboard for visualization
- Scheduled data cleanup tasks

## Configuration

1. The analytics system is configured through `config/analytics_config.yml`.
2. Key configuration options:
   - Event batching settings
   - Data retention policies
   - Tracking preferences
   - Dashboard settings
   - Rate limiting
   - Custom metrics

## Database Setup

The analytics system requires MongoDB for data storage. Ensure the MongoDB configuration in `config/database_config.yml` is properly set up.

```yaml
# Example MongoDB configuration
mongodb:
  uri: "mongodb://localhost:27017/"
  database: "egypt_chatbot"
  collections:
    analytics_events: "analytics_events"
    analytics_aggregates: "analytics_aggregates"
```

## Scheduled Tasks

### Analytics Data Cleanup

To keep the database size manageable, old analytics data is automatically cleaned up based on the retention settings.

To set up the scheduled cleanup task:

1. Make the cleanup script executable:

   ```bash
   chmod +x scripts/analytics_cron.sh
   ```

2. Add the task to crontab to run daily at 2 AM:

   ```bash
   crontab -e
   ```

3. Add the following line:
   ```
   0 2 * * * /path/to/egypt-chatbot/scripts/analytics_cron.sh
   ```

## Dashboard Access

The analytics dashboard is available at `/admin/analytics` and requires admin authentication.

To access the dashboard:

1. Ensure you have admin credentials
2. Log in to the admin interface
3. Navigate to Analytics in the menu

## API Endpoints

The analytics API is accessible at `/api/analytics/*` with the following endpoints:

- `/api/analytics/stats/overview` - Get overall statistics
- `/api/analytics/stats/daily` - Get daily statistics
- `/api/analytics/stats/session/<session_id>` - Get session statistics
- `/api/analytics/stats/intents` - Get intent distribution
- `/api/analytics/stats/entities` - Get entity distribution
- `/api/analytics/stats/feedback` - Get feedback statistics
- `/api/analytics/stats/messages` - Get message statistics

Most endpoints require admin authentication, except for session-specific endpoints.

## Tracking Events

The analytics system automatically tracks events through the ChatHandler, but you can also manually track events:

```python
# Example: Tracking a custom event
app.analytics.track_event(
    event_type="custom_event",
    event_data={"key": "value"},
    session_id="session123",
    user_id="user456"
)
```

## Data Export

To export analytics data:

1. Go to the analytics dashboard
2. Use the export feature in the top-right corner
3. Select the date range and format (CSV or JSON)
4. Click "Export"

## Troubleshooting

### Missing Analytics Data

If analytics data isn't appearing:

1. Check MongoDB connection in the logs
2. Verify that the analytics is initialized in app.py
3. Ensure event tracking is enabled in the configuration
4. Check the browser console for dashboard-related errors

### High Database Usage

If MongoDB usage is too high:

1. Reduce the retention period in `analytics_config.yml`
2. Run the cleanup task manually:
   ```bash
   python -m src.tasks.analytics_cleanup
   ```
3. Consider increasing the `flush_interval` to reduce write frequency

## Additional Resources

- [MongoDB Documentation](https://docs.mongodb.com/)
- [Chart.js Documentation](https://www.chartjs.org/docs/latest/) (used for dashboard visualizations)
- [Flask Blueprint Documentation](https://flask.palletsprojects.com/en/2.2.x/blueprints/)
