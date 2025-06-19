export interface ChatMessage {
  id: string;
  type: "text" | "card" | "welcome";
  content: string;
  image?: string;
  isBot: boolean;
  timestamp: Date;
}

export interface ImageCard {
  id: string;
  image: string;
  text: string;
  category?: "attractions" | "hotels" | "restaurants" | "activities";
}

export interface WidgetConfig {
  apiUrl: string;
  theme: "light" | "dark";
  position: "bottom-right" | "bottom-left";
  language: "en" | "ar";
  autoOpen: boolean;
  greeting?: string;
}

export interface TabState {
  activeTab: "chat" | "trip";
}

export interface TripData {
  id: string;
  title: string;
  destinations: string[];
  startDate?: Date;
  endDate?: Date;
  coverImage?: string;
}
