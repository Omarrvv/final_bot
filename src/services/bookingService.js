class BookingService {
  constructor() {
    this.tours = [];
    this.hotels = [];
  }

  async fetchTours() {
    // Fetch available tours from API
    const response = await fetch('/api/tours');
    this.tours = await response.json();
    return this.tours;
  }

  async fetchHotels() {
    // Fetch available hotels from API
    const response = await fetch('/api/hotels');
    this.hotels = await response.json();
    return this.hotels;
  }

  async bookTour(tourId, userId, date) {
    const response = await fetch('/api/book/tour', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ tourId, userId, date }),
    });
    return response.json();
  }

  async bookHotel(hotelId, userId, checkInDate, checkOutDate) {
    const response = await fetch('/api/book/hotel', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ hotelId, userId, checkInDate, checkOutDate }),
    });
    return response.json();
  }
}

export default new BookingService();
