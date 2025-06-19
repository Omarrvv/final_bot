import React from "react";

interface TripViewProps {
  onTabChange: (tab: "chat" | "trip") => void;
}

const TripView: React.FC<TripViewProps> = ({ onTabChange }) => {
  return (
    <div className="h-full flex flex-col p-6">
      <div className="text-center mb-6">
        <div className="text-3xl font-bold text-blue-600 mb-4">
          Plan your Egyptian adventure
        </div>
        <button className="text-xs text-blue-600 border border-blue-200 rounded-full px-4 py-2 hover:bg-blue-50 transition-colors flex items-center space-x-2 mx-auto">
          <svg
            className="w-3 h-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
            />
          </svg>
          <span>Log in to save your itinerary</span>
        </button>
      </div>

      <div className="flex-1 space-y-4">
        {/* Main image card */}
        <div className="relative rounded-2xl overflow-hidden shadow-sm">
          <img
            src="https://images.unsplash.com/photo-1562679299-8d0f689fc122?w=400"
            alt="Explore Egypt's treasures"
            className="w-full h-48 object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
          <div className="absolute bottom-6 left-6 right-6">
            <div className="text-white font-semibold text-base">
              Explore Egypt's ancient treasures
            </div>
          </div>
        </div>

        {/* Smaller image cards */}
        <div className="grid grid-cols-2 gap-3">
          <div className="relative rounded-xl overflow-hidden shadow-sm">
            <img
              src="https://images.unsplash.com/photo-1572252009286-268acec5ca0a?w=200"
              alt="Luxor Temple"
              className="w-full h-24 object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
          </div>
          <div className="relative rounded-xl overflow-hidden shadow-sm">
            <img
              src="https://images.unsplash.com/photo-1594477778796-0e6bee2fa70f?w=200"
              alt="Red Sea diving"
              className="w-full h-24 object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
          </div>
        </div>
      </div>

      {/* CTA Button */}
      <button
        onClick={() => onTabChange("chat")}
        className="w-full bg-red-700 text-white py-4 rounded-xl font-medium mt-6 hover:bg-red-800 transition-colors"
      >
        Take me to the chat
      </button>
    </div>
  );
};

export default TripView;
