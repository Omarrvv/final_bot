/**
 * Analytics Dashboard JavaScript
 * Handles fetching and visualizing analytics data for the Egypt Tourism Chatbot
 */

// Global chart objects
let overviewChart = null;
let dailyChart = null;
let intentDistributionChart = null;
let messageTypeChart = null;
let feedbackChart = null;
let languageChart = null;

// Default time period
let timePeriod = 30;

/**
 * Initialize the dashboard
 */
function initDashboard() {
  // Add event listeners
  document
    .getElementById("time-period-selector")
    .addEventListener("change", function () {
      timePeriod = parseInt(this.value);
      refreshAllCharts();
    });

  // Initialize charts
  initOverviewStats();
  initDailyStats();
  initIntentDistribution();
  initMessageStats();
  initFeedbackStats();

  // Set up refresh interval (every 5 minutes)
  setInterval(refreshAllCharts, 300000);
}

/**
 * Refresh all charts
 */
function refreshAllCharts() {
  initOverviewStats();
  initDailyStats();
  initIntentDistribution();
  initMessageStats();
  initFeedbackStats();
}

/**
 * Initialize overview statistics
 */
function initOverviewStats() {
  fetch(`/api/analytics/stats/overview`)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to fetch overview stats");
      }
      return response.json();
    })
    .then((data) => {
      // Update overview cards
      document.getElementById("total-sessions").textContent =
        data.total_sessions;
      document.getElementById("total-users").textContent = data.total_users;
      document.getElementById("total-messages").textContent =
        data.total_messages;
      document.getElementById("avg-session-length").textContent = formatTime(
        data.average_session_length
      );

      // Create overview chart
      createOverviewChart(data);
    })
    .catch((error) => {
      console.error("Error fetching overview stats:", error);
      showError("overview-container", "Failed to load overview statistics");
    });
}

/**
 * Create the overview chart
 */
function createOverviewChart(data) {
  const ctx = document.getElementById("overview-chart").getContext("2d");

  // Destroy existing chart if it exists
  if (overviewChart) {
    overviewChart.destroy();
  }

  // Create new chart
  overviewChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Messages"],
      datasets: [
        {
          label: "User Messages",
          data: [data.user_messages],
          backgroundColor: "rgba(54, 162, 235, 0.6)",
        },
        {
          label: "Bot Messages",
          data: [data.bot_messages],
          backgroundColor: "rgba(75, 192, 192, 0.6)",
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: "Count",
          },
        },
      },
      plugins: {
        title: {
          display: true,
          text: "Message Distribution",
        },
      },
    },
  });

  // Create feedback chart
  const feedbackCtx = document
    .getElementById("feedback-overview-chart")
    .getContext("2d");

  // Destroy existing chart if it exists
  if (feedbackChart) {
    feedbackChart.destroy();
  }

  // Create new chart
  feedbackChart = new Chart(feedbackCtx, {
    type: "doughnut",
    data: {
      labels: ["Positive", "Negative"],
      datasets: [
        {
          data: [data.feedback.positive, data.feedback.negative],
          backgroundColor: [
            "rgba(75, 192, 192, 0.6)",
            "rgba(255, 99, 132, 0.6)",
          ],
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: "User Feedback",
        },
      },
    },
  });
}

/**
 * Initialize daily statistics
 */
function initDailyStats() {
  fetch(`/api/analytics/stats/daily?days=${timePeriod}`)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to fetch daily stats");
      }
      return response.json();
    })
    .then((data) => {
      createDailyChart(data);
    })
    .catch((error) => {
      console.error("Error fetching daily stats:", error);
      showError("daily-chart-container", "Failed to load daily statistics");
    });
}

/**
 * Create the daily stats chart
 */
function createDailyChart(data) {
  const ctx = document.getElementById("daily-chart").getContext("2d");

  // Extract data for chart
  const dates = data.map((day) => day.date);
  const sessions = data.map((day) => day.total_sessions);
  const messages = data.map((day) => day.total_messages);

  // Destroy existing chart if it exists
  if (dailyChart) {
    dailyChart.destroy();
  }

  // Create new chart
  dailyChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: dates,
      datasets: [
        {
          label: "Sessions",
          data: sessions,
          borderColor: "rgba(54, 162, 235, 1)",
          backgroundColor: "rgba(54, 162, 235, 0.1)",
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          yAxisID: "y",
        },
        {
          label: "Messages",
          data: messages,
          borderColor: "rgba(75, 192, 192, 1)",
          backgroundColor: "rgba(75, 192, 192, 0.1)",
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          yAxisID: "y1",
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        x: {
          title: {
            display: true,
            text: "Date",
          },
        },
        y: {
          beginAtZero: true,
          position: "left",
          title: {
            display: true,
            text: "Sessions",
          },
        },
        y1: {
          beginAtZero: true,
          position: "right",
          grid: {
            drawOnChartArea: false,
          },
          title: {
            display: true,
            text: "Messages",
          },
        },
      },
      plugins: {
        title: {
          display: true,
          text: "Daily Activity",
        },
      },
    },
  });
}

/**
 * Initialize intent distribution chart
 */
function initIntentDistribution() {
  fetch("/api/analytics/stats/intents")
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to fetch intent distribution");
      }
      return response.json();
    })
    .then((data) => {
      createIntentDistributionChart(data);
    })
    .catch((error) => {
      console.error("Error fetching intent distribution:", error);
      showError("intent-chart-container", "Failed to load intent distribution");
    });
}

/**
 * Create the intent distribution chart
 */
function createIntentDistributionChart(data) {
  const ctx = document.getElementById("intent-chart").getContext("2d");

  // Extract data for chart
  const intents = Object.keys(data.intents);
  const counts = Object.values(data.intents);

  // Limit to top 10 intents
  const topIntents = intents.slice(0, 10);
  const topCounts = counts.slice(0, 10);

  // Destroy existing chart if it exists
  if (intentDistributionChart) {
    intentDistributionChart.destroy();
  }

  // Create new chart
  intentDistributionChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: topIntents,
      datasets: [
        {
          label: "Count",
          data: topCounts,
          backgroundColor: "rgba(153, 102, 255, 0.6)",
          borderColor: "rgba(153, 102, 255, 1)",
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      indexAxis: "y",
      scales: {
        x: {
          beginAtZero: true,
          title: {
            display: true,
            text: "Count",
          },
        },
      },
      plugins: {
        title: {
          display: true,
          text: "Top Intents",
        },
      },
    },
  });
}

/**
 * Initialize message statistics
 */
function initMessageStats() {
  fetch(`/api/analytics/stats/messages?days=${timePeriod}`)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to fetch message stats");
      }
      return response.json();
    })
    .then((data) => {
      // Update message stats cards
      document.getElementById("total-messages-period").textContent = data.total;
      document.getElementById("user-messages-period").textContent =
        data.user_messages;
      document.getElementById("bot-messages-period").textContent =
        data.bot_messages;
      document.getElementById("avg-user-length").textContent =
        Math.round(data.average_length.user) + " chars";
      document.getElementById("avg-bot-length").textContent =
        Math.round(data.average_length.bot) + " chars";

      // Create message type chart
      createMessageTypeChart(data);

      // Create language chart
      createLanguageChart(data);
    })
    .catch((error) => {
      console.error("Error fetching message stats:", error);
      showError("message-stats-container", "Failed to load message statistics");
    });
}

/**
 * Create message type chart
 */
function createMessageTypeChart(data) {
  const ctx = document.getElementById("message-type-chart").getContext("2d");

  // Destroy existing chart if it exists
  if (messageTypeChart) {
    messageTypeChart.destroy();
  }

  // Create new chart
  messageTypeChart = new Chart(ctx, {
    type: "pie",
    data: {
      labels: ["User Messages", "Bot Messages"],
      datasets: [
        {
          data: [data.user_messages, data.bot_messages],
          backgroundColor: [
            "rgba(54, 162, 235, 0.6)",
            "rgba(75, 192, 192, 0.6)",
          ],
          borderColor: ["rgba(54, 162, 235, 1)", "rgba(75, 192, 192, 1)"],
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: "Message Distribution",
        },
      },
    },
  });
}

/**
 * Create language chart
 */
function createLanguageChart(data) {
  const ctx = document.getElementById("language-chart").getContext("2d");

  // Destroy existing chart if it exists
  if (languageChart) {
    languageChart.destroy();
  }

  // Create new chart
  languageChart = new Chart(ctx, {
    type: "pie",
    data: {
      labels: ["English", "Arabic"],
      datasets: [
        {
          data: [data.languages.en, data.languages.ar],
          backgroundColor: [
            "rgba(255, 159, 64, 0.6)",
            "rgba(153, 102, 255, 0.6)",
          ],
          borderColor: ["rgba(255, 159, 64, 1)", "rgba(153, 102, 255, 1)"],
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: "Language Distribution",
        },
      },
    },
  });
}

/**
 * Initialize feedback statistics
 */
function initFeedbackStats() {
  fetch(`/api/analytics/stats/feedback?days=${timePeriod}`)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to fetch feedback stats");
      }
      return response.json();
    })
    .then((data) => {
      // Update feedback stats cards
      document.getElementById("total-feedback").textContent = data.total;
      document.getElementById("positive-feedback").textContent = data.positive;
      document.getElementById("negative-feedback").textContent = data.negative;
      document.getElementById("positive-percentage").textContent =
        data.positive_percentage.toFixed(1) + "%";

      // Add feedback comments to list
      const commentsList = document.getElementById("feedback-comments");
      commentsList.innerHTML = "";

      if (data.comments.length === 0) {
        commentsList.innerHTML =
          '<li class="list-group-item">No comments available</li>';
      } else {
        // Sort comments by timestamp (newest first)
        data.comments.sort(
          (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
        );

        // Display the 10 most recent comments
        const recentComments = data.comments.slice(0, 10);

        recentComments.forEach((comment) => {
          const li = document.createElement("li");
          li.className = "list-group-item";

          // Add rating indicator
          const ratingClass =
            comment.rating > 0 ? "text-success" : "text-danger";
          const ratingIcon = comment.rating > 0 ? "thumbs-up" : "thumbs-down";

          // Format date
          const date = new Date(comment.timestamp);
          const formattedDate =
            date.toLocaleDateString() + " " + date.toLocaleTimeString();

          li.innerHTML = `
                        <div class="d-flex justify-content-between">
                            <span>
                                <i class="bi bi-${ratingIcon} ${ratingClass}"></i> 
                                ${escapeHtml(comment.comment)}
                            </span>
                            <small class="text-muted">${formattedDate}</small>
                        </div>
                    `;

          commentsList.appendChild(li);
        });
      }
    })
    .catch((error) => {
      console.error("Error fetching feedback stats:", error);
      showError("feedback-container", "Failed to load feedback statistics");
    });
}

/**
 * Format time in seconds to a readable string
 */
function formatTime(seconds) {
  if (!seconds) return "0s";

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);

  if (minutes === 0) {
    return `${remainingSeconds}s`;
  } else {
    return `${minutes}m ${remainingSeconds}s`;
  }
}

/**
 * Show error message in a container
 */
function showError(containerId, message) {
  const container = document.getElementById(containerId);
  container.innerHTML = `
        <div class="alert alert-danger" role="alert">
            <i class="bi bi-exclamation-triangle-fill"></i> 
            ${message}
        </div>
    `;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(unsafe) {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Initialize the dashboard when the page loads
document.addEventListener("DOMContentLoaded", initDashboard);
