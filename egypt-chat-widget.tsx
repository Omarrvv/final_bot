"use client"

import { useState } from "react"
import { MessageCircle, X, Settings, Mic, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export default function Component() {
  const [isOpen, setIsOpen] = useState(false)
  const [activeTab, setActiveTab] = useState("Chat")

  return (
    <div
      className="min-h-screen bg-gray-100 relative"
      style={{
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        fontWeight: "400",
      }}
    >
      {/* Demo background content */}
      <div className="p-8">
        <h1 className="text-2xl font-medium mb-4">Visit Egypt Website Demo</h1>
        <p className="text-gray-600 font-normal">Click the chat widget to see the expanded interface.</p>
      </div>

      {/* Chat Widget */}
      <div className="fixed bottom-8 right-8 z-50">
        {isOpen ? (
          <div className="bg-white rounded-3xl shadow-2xl border border-gray-200 w-[480px] h-[820px] flex flex-col overflow-hidden">
            {/* Header with fully visible rounded top */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white">
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="sm" className="p-2">
                  <Settings className="w-4 h-4 text-gray-500" />
                </Button>
              </div>

              <div className="flex bg-gray-100 rounded-full p-1">
                <button
                  onClick={() => setActiveTab("Chat")}
                  className={`px-6 py-2 rounded-full text-sm font-normal transition-colors ${
                    activeTab === "Chat" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
                  }`}
                >
                  Chat
                </button>
                <button
                  onClick={() => setActiveTab("My Trip")}
                  className={`px-6 py-2 rounded-full text-sm font-normal transition-colors ${
                    activeTab === "My Trip" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
                  }`}
                >
                  My Trip
                </button>
              </div>

              <Button variant="ghost" size="sm" onClick={() => setIsOpen(false)} className="p-2">
                <X className="w-4 h-4 text-gray-500" />
              </Button>
            </div>

            {/* Chat Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {activeTab === "Chat" ? (
                <>
                  {/* Welcome Message */}
                  <div className="text-center space-y-4">
                    <h2 className="text-3xl font-normal text-[#DC143C]">Ahlan wa Sahlan!</h2>
                    <p className="text-base text-gray-600 leading-relaxed px-4 font-normal">
                      I'm Visit Egypt's travel expert. Use the prompts below for quick answers or ask me anything about
                      Egypt!
                    </p>
                  </div>

                  {/* Login Button - Properly sized with better spacing */}
                  <div className="flex justify-center pt-2">
                    <Button
                      variant="outline"
                      className="text-[#DC143C] border-[#DC143C] hover:bg-[#DC143C] hover:text-white px-6 py-2 text-sm font-normal"
                    >
                      <User className="w-4 h-4 mr-2" />
                      Log in to view your existing trip
                    </Button>
                  </div>

                  {/* Main Featured Card - Large with Egyptian Image */}
                  <div className="relative rounded-xl overflow-hidden cursor-pointer hover:shadow-md transition-shadow">
                    <img
                      src="https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?w=450&h=280&fit=crop&auto=format"
                      alt="Traditional felucca boats sailing on the Nile River at sunset"
                      className="w-full h-48 object-cover"
                      onError={(e) => {
                        e.currentTarget.src = "/placeholder.svg?height=280&width=450&text=Nile+River+Cruise+at+Sunset"
                      }}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-black/20 to-transparent"></div>
                    <div className="absolute bottom-4 left-4">
                      <p className="text-white font-medium text-lg">Best Nile cruise experiences?</p>
                    </div>
                  </div>

                  {/* Suggestion Cards - 2 Column Grid with Egyptian Images */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 rounded-xl p-4 cursor-pointer hover:bg-gray-100 transition-colors">
                      <img
                        src="https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=180&h=120&fit=crop&auto=format"
                        alt="Traditional Khan El Khalili bazaar with spices and crafts"
                        className="w-full h-24 object-cover rounded-lg mb-3"
                        onError={(e) => {
                          e.currentTarget.src = "/placeholder.svg?height=120&width=180&text=Khan+El+Khalili"
                        }}
                      />
                      <p className="text-sm font-normal text-gray-800">Best shopping offers</p>
                    </div>

                    <div className="bg-gray-50 rounded-xl p-4 cursor-pointer hover:bg-gray-100 transition-colors">
                      <img
                        src="https://images.unsplash.com/photo-1568322445389-f64ac2515020?w=180&h=120&fit=crop&auto=format"
                        alt="Family exploring the Great Pyramids of Giza"
                        className="w-full h-24 object-cover rounded-lg mb-3"
                        onError={(e) => {
                          e.currentTarget.src = "/placeholder.svg?height=120&width=180&text=Pyramids+Family+Tour"
                        }}
                      />
                      <p className="text-sm font-normal text-gray-800">Find family activities</p>
                    </div>
                  </div>

                  {/* AI Assistant Card */}
                  <div className="relative rounded-xl overflow-hidden cursor-pointer hover:shadow-md transition-shadow">
                    <div className="bg-gradient-to-br from-amber-400 via-orange-500 to-red-600 h-32 flex items-center justify-center relative">
                      <div className="absolute inset-0 bg-black bg-opacity-10"></div>
                      <div className="flex items-center gap-4 z-10">
                        <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center">
                          <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
                            <div className="w-4 h-4 bg-gradient-to-br from-amber-500 to-red-500 rounded-full"></div>
                          </div>
                        </div>
                        <div className="w-16 h-16 bg-white/30 backdrop-blur-sm rounded-full flex items-center justify-center">
                          <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center">
                            <MessageCircle className="w-5 h-5 text-orange-500" />
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="absolute bottom-3 left-4">
                      <p className="text-white font-medium text-base">Discover hidden gems with AI</p>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  {/* My Trip Content */}
                  <div className="text-center space-y-6">
                    <h2 className="text-3xl font-normal text-[#DC143C] leading-tight">
                      Plan your next
                      <br />
                      Egyptian adventure
                    </h2>

                    {/* Login Button - Properly sized */}
                    <Button
                      variant="outline"
                      className="text-[#DC143C] border-[#DC143C] hover:bg-[#DC143C] hover:text-white px-6 py-2 text-sm font-normal"
                    >
                      <User className="w-4 h-4 mr-2" />
                      Log in to view trip
                    </Button>
                  </div>

                  {/* Main Trip Planning Card with Egyptian Image */}
                  <div className="relative rounded-xl overflow-hidden cursor-pointer hover:shadow-md transition-shadow">
                    <div className="bg-gray-100 h-48 flex items-center justify-center">
                      <div className="w-12 h-12 text-gray-400">
                        <svg
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1"
                          className="w-full h-full"
                        >
                          <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                          <circle cx="8.5" cy="8.5" r="1.5" />
                          <polyline points="21,15 16,10 5,21" />
                        </svg>
                      </div>
                    </div>
                    <div className="p-4 bg-white">
                      <p className="text-base font-normal text-gray-800">Plan detailed ancient Egypt tour</p>
                    </div>
                  </div>

                  {/* Trip Suggestion Cards with Egyptian Images */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white rounded-xl overflow-hidden cursor-pointer hover:shadow-md transition-shadow border border-gray-100">
                      <img
                        src="https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=180&h=120&fit=crop&auto=format"
                        alt="Red Sea coral reef diving with tropical fish"
                        className="w-full h-24 object-cover"
                        onError={(e) => {
                          e.currentTarget.src = "/placeholder.svg?height=120&width=180&text=Red+Sea+Diving"
                        }}
                      />
                      <div className="p-3">
                        <p className="text-sm font-normal text-gray-800">Plan a 5-day Red Sea diving trip</p>
                      </div>
                    </div>

                    <div className="bg-white rounded-xl overflow-hidden cursor-pointer hover:shadow-md transition-shadow border border-gray-100">
                      <img
                        src="https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=180&h=120&fit=crop&auto=format"
                        alt="Traditional Egyptian street food and spices in Cairo market"
                        className="w-full h-24 object-cover"
                        onError={(e) => {
                          e.currentTarget.src = "/placeholder.svg?height=120&width=180&text=Cairo+Food+Tour"
                        }}
                      />
                      <div className="p-3">
                        <p className="text-sm font-normal text-gray-800">Plan a 3-day Cairo food tour</p>
                      </div>
                    </div>
                  </div>

                  {/* Take me to chat button */}
                  <Button className="w-full bg-[#B8860B] hover:bg-[#A0750A] text-white py-4 rounded-xl font-normal text-base">
                    Take me to the chat
                  </Button>
                </>
              )}
            </div>

            {/* Input Area */}
            <div className="p-6 border-t border-gray-200">
              <div className="flex items-center gap-3 bg-gray-50 rounded-full px-5 py-3">
                <Input
                  placeholder="Start a conversation..."
                  className="flex-1 border-none bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 placeholder:text-gray-500 text-base font-normal"
                />
                <Button variant="ghost" size="sm" className="p-2 hover:bg-gray-200 rounded-full">
                  <Mic className="w-5 h-5 text-gray-500" />
                </Button>
                <div className="w-10 h-10 bg-[#DC143C] rounded-full flex items-center justify-center">
                  <div className="w-7 h-7 bg-white rounded-full flex items-center justify-center">
                    <User className="w-4 h-4 text-[#DC143C]" />
                  </div>
                </div>
              </div>
              <p className="text-sm text-gray-500 text-center mt-3 font-normal">
                AI assistance in use. Check official travel sources
              </p>
            </div>
          </div>
        ) : (
          /* Collapsed widget with milky background and circular Egypt banner */
          <div
            className="bg-gray-50/90 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 p-3 cursor-pointer hover:shadow-xl transition-shadow w-64"
            onClick={() => setIsOpen(true)}
          >
            <div className="flex items-center gap-3">
              {/* Circular Egypt Banner */}
              <div className="w-12 h-12 bg-[#DC143C] rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-white font-medium text-sm">EGYPT</span>
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 mb-1">Need some help?</p>
                <p className="text-xs text-gray-600 font-normal">Let's chat</p>
              </div>

              {/* Online indicator */}
              <div className="w-3 h-3 bg-green-400 rounded-full flex-shrink-0"></div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
