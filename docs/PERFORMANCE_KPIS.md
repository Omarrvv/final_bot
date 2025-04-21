# Key Performance Indicators (KPIs)

This document defines the key performance indicators for the Egypt Tourism Chatbot.

## Response Time

| Metric            | Target | Critical Threshold |
| ----------------- | ------ | ------------------ |
| P95 Response Time | < 2s   | > 5s               |
| P99 Response Time | < 4s   | > 8s               |
| Avg Response Time | < 1s   | > 3s               |

## Error Rates

| Metric                | Target | Critical Threshold |
| --------------------- | ------ | ------------------ |
| API Error Rate (5xx)  | < 1%   | > 5%               |
| NLP Processing Errors | < 2%   | > 8%               |
| KB Query Failures     | < 0.5% | > 3%               |

## Database Performance

| Metric                      | Target | Critical Threshold |
| --------------------------- | ------ | ------------------ |
| Avg Query Time              | < 50ms | > 200ms            |
| Slow Queries (>100ms)       | < 5%   | > 15%              |
| Connection Pool Utilization | < 70%  | > 90%              |

## User Experience

| Metric                      | Target  |
| --------------------------- | ------- |
| Intent Recognition Accuracy | > 85%   |
| Entity Extraction Accuracy  | > 80%   |
| User Satisfaction Rating    | > 4.2/5 |

## Resource Utilization

| Metric          | Target | Critical Threshold |
| --------------- | ------ | ------------------ |
| CPU Utilization | < 60%  | > 85%              |
| Memory Usage    | < 70%  | > 90%              |
| Disk I/O        | < 70%  | > 90%              |

## Monitoring Frequency

- Real-time: Error rates, Response times
- Hourly: Resource utilization
- Daily: Database performance, NLP accuracy
- Weekly: User satisfaction

## Alerting Thresholds

Alerts should be triggered when:

- Any metric exceeds its critical threshold for more than 5 minutes
- Error rate suddenly increases by more than 300% over baseline
- P95 response time increases by more than 100% over baseline
- Database connection failures occur
