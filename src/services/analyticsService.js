class AnalyticsService {
  constructor() {
    this.queries = [];
    this.feedback = [];
  }

  trackQuery(query) {
    this.queries.push({
      query,
      timestamp: new Date().toISOString()
    });
  }

  trackFeedback(userId, rating, comment) {
    this.feedback.push({
      userId,
      rating,
      comment,
      timestamp: new Date().toISOString()
    });
  }

  getQueryStats() {
    const queryCounts = this.queries.reduce((acc, { query }) => {
      acc[query] = (acc[query] || 0) + 1;
      return acc;
    }, {});
    return Object.entries(queryCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);
  }

  getFeedbackStats() {
    const total = this.feedback.length;
    if (total === 0) return null;

    const averageRating = this.feedback.reduce((sum, { rating }) => sum + rating, 0) / total;
    return {
      averageRating: parseFloat(averageRating.toFixed(2)),
      totalFeedbacks: total
    };
  }
}

export default new AnalyticsService();
