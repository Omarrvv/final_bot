import 'regenerator-runtime/runtime';
import BookingService from '../src/services/bookingService.js';
import AnalyticsService from '../src/services/analyticsService.js';

document.addEventListener('DOMContentLoaded', () => {
  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');
  const voiceBtn = document.getElementById('voice-btn');
  const chatWindow = document.getElementById('chat-window');
  const userInputElement = document.getElementById('user-input');
  const chatBoxElement = document.getElementById('chat-box');
  const imageContainerElement = document.getElementById('image-container');

  sendBtn.addEventListener('click', () => {
    sendMessage();
  });

  voiceBtn.addEventListener('click', () => {
    startVoiceInput();
  });

  function displayImage(imageUrl) {
    imageContainerElement.innerHTML = `<img src="${imageUrl}" alt="Attraction Image" class="attraction-image">`;
  }

  function startVoiceInput() {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.start();

    recognition.onresult = function(event) {
      const transcript = event.results[0][0].transcript;
      userInputElement.value = transcript;
      sendMessage();
    };
  }

  function speakResponse(response) {
    const utterance = new SpeechSynthesisUtterance(response);
    window.speechSynthesis.speak(utterance);
  }

  function sendMessage() {
    const userInput = userInputElement.value;
    if (userInput.trim() === '') return;

    // Track the query
    AnalyticsService.trackQuery(userInput);

    // Add user message to chat
    chatBoxElement.innerHTML += `<div class="user-message">${userInput}</div>`;

    // Get bot response
    fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: userInput }),
    })
    .then(response => response.json())
    .then(data => {
      // Add bot response to chat
      chatBoxElement.innerHTML += `<div class="bot-message">${data.response}</div>`;
      
      // Display image if available
      if (data.imageUrl) {
        displayImage(data.imageUrl);
      }

      // Speak the response
      speakResponse(data.response);

      // Scroll to bottom
      chatBoxElement.scrollTop = chatBoxElement.scrollHeight;
    });

    // Clear input
    userInputElement.value = '';
  }

  // Add booking CSS
  const linkElement = document.createElement('link');
  linkElement.rel = 'stylesheet';
  linkElement.href = '/css/booking.css';
  document.head.appendChild(linkElement);

  // Implement getCurrentUserId function
  function getCurrentUserId() {
    // For now, return a mock user ID
    // In a real application, this would come from authentication
    return 'mock-user-id';
  }

  // Add booking buttons to the UI
  const bookingContainer = document.createElement('div');
  bookingContainer.id = 'booking-container';
  bookingContainer.innerHTML = `
    <button id="book-tour-btn">Book a Tour</button>
    <button id="book-hotel-btn">Book a Hotel</button>
  `;
  document.body.appendChild(bookingContainer);

  // Handle tour booking
  const bookTourBtn = document.getElementById('book-tour-btn');
  bookTourBtn.addEventListener('click', async () => {
    const tours = await BookingService.fetchTours();
    // Display tours and handle selection
    const tourList = tours.map(tour => `
      <div class="tour-item">
        <h3>${tour.name}</h3>
        <p>${tour.description}</p>
        <button onclick="selectTour('${tour.id}')">Select</button>
      </div>
    `).join('');
    document.getElementById('chat-box').innerHTML += tourList;
  });

  // Handle hotel booking
  const bookHotelBtn = document.getElementById('book-hotel-btn');
  bookHotelBtn.addEventListener('click', async () => {
    const hotels = await BookingService.fetchHotels();
    // Display hotels and handle selection
    const hotelList = hotels.map(hotel => `
      <div class="hotel-item">
        <h3>${hotel.name}</h3>
        <p>${hotel.description}</p>
        <button onclick="selectHotel('${hotel.id}')">Select</button>
      </div>
    `).join('');
    document.getElementById('chat-box').innerHTML += hotelList;
  });

  // Handle tour selection
  function selectTour(tourId) {
    // Show booking form
    const bookingForm = `
      <div id="tour-booking-form">
        <label for="tour-date">Select Date:</label>
        <input type="date" id="tour-date">
        <button onclick="confirmTourBooking('${tourId}')">Confirm Booking</button>
      </div>
    `;
    document.getElementById('chat-box').innerHTML += bookingForm;
  }

  // Handle hotel selection
  function selectHotel(hotelId) {
    // Show booking form
    const bookingForm = `
      <div id="hotel-booking-form">
        <label for="check-in-date">Check-in Date:</label>
        <input type="date" id="check-in-date">
        <label for="check-out-date">Check-out Date:</label>
        <input type="date" id="check-out-date">
        <button onclick="confirmHotelBooking('${hotelId}')">Confirm Booking</button>
      </div>
    `;
    document.getElementById('chat-box').innerHTML += bookingForm;
  }

  // Confirm tour booking
  async function confirmTourBooking(tourId) {
    const date = document.getElementById('tour-date').value;
    const userId = getCurrentUserId(); 
    const result = await BookingService.bookTour(tourId, userId, date);
    document.getElementById('chat-box').innerHTML += `
      <div class="booking-confirmation">
        <p>${result.message}</p>
      </div>
    `;
  }

  // Confirm hotel booking
  async function confirmHotelBooking(hotelId) {
    const checkInDate = document.getElementById('check-in-date').value;
    const checkOutDate = document.getElementById('check-out-date').value;
    const userId = getCurrentUserId(); 
    const result = await BookingService.bookHotel(hotelId, userId, checkInDate, checkOutDate);
    document.getElementById('chat-box').innerHTML += `
      <div class="booking-confirmation">
        <p>${result.message}</p>
      </div>
    `;
  }

  // Add feedback buttons
  const feedbackContainer = document.createElement('div');
  feedbackContainer.id = 'feedback-container';
  feedbackContainer.innerHTML = `
    <p>Was this helpful?</p>
    <button id="feedback-yes">Yes</button>
    <button id="feedback-no">No</button>
  `;
  document.body.appendChild(feedbackContainer);

  // Handle feedback
  const feedbackYesBtn = document.getElementById('feedback-yes');
  const feedbackNoBtn = document.getElementById('feedback-no');

  feedbackYesBtn.addEventListener('click', () => {
    AnalyticsService.trackFeedback(getCurrentUserId(), 5, 'Positive feedback');
    showFeedbackMessage('Thank you for your feedback!');
  });

  feedbackNoBtn.addEventListener('click', () => {
    const comment = prompt('What could we improve?');
    AnalyticsService.trackFeedback(getCurrentUserId(), 1, comment);
    showFeedbackMessage('Thank you for helping us improve!');
  });

  function showFeedbackMessage(message) {
    const feedbackMessage = document.createElement('div');
    feedbackMessage.className = 'feedback-message';
    feedbackMessage.textContent = message;
    feedbackContainer.appendChild(feedbackMessage);
    setTimeout(() => feedbackMessage.remove(), 3000);
  }
});
