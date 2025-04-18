import AnalyticsService from '../src/services/analyticsService.js';
import BookingService from '../src/services/bookingService.js';

describe('Chatbot Services', () => {
  beforeEach(() => {
    // Reset services before each test
    AnalyticsService.queries = [];
    AnalyticsService.feedback = [];
    BookingService.tours = [];
    BookingService.hotels = [];
  });

  test('should track queries correctly', () => {
    AnalyticsService.trackQuery('test query');
    expect(AnalyticsService.queries.length).toBe(1);
    expect(AnalyticsService.queries[0].query).toBe('test query');
  });

  test('should track feedback correctly', () => {
    AnalyticsService.trackFeedback('user1', 5, 'Great service!');
    expect(AnalyticsService.feedback.length).toBe(1);
    expect(AnalyticsService.feedback[0].rating).toBe(5);
  });

  test('should fetch and book tours', async () => {
    BookingService.tours = [{ id: 'tour1', name: 'Test Tour' }];
    const result = await BookingService.bookTour('tour1', 'user1', '2025-01-01');
    expect(result).toBeDefined();
  });

  test('should fetch and book hotels', async () => {
    BookingService.hotels = [{ id: 'hotel1', name: 'Test Hotel' }];
    const result = await BookingService.bookHotel('hotel1', 'user1', '2025-01-01', '2025-01-05');
    expect(result).toBeDefined();
  });
});
