#!/bin/bash

echo "🇪🇬 KARIM'S WEBSITE - EGYPT TOURISM CHATBOT DEMO"
echo "================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${2}${1}${NC}"
}

print_status "🚀 Starting Karim's Website Demo..." $CYAN
echo ""

# Kill any existing processes
print_status "🔄 Cleaning up existing processes..." $YELLOW
lsof -ti:5050 | xargs kill -9 2>/dev/null || true
lsof -ti:8080 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
print_status "✅ Ports cleared (5050, 8080, 3000)" $GREEN
echo ""

# Build the React widget
print_status "📦 Building React Widget..." $BLUE
cd react-egypt-chatbot-widget

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    print_status "📥 Installing React widget dependencies..." $YELLOW
    npm install
fi

# Build the widget
print_status "🔨 Building production widget..." $YELLOW
npm run build

if [ ! -f "build/egypt-tourism-widget.min.js" ]; then
    print_status "❌ Widget build failed! Expected file not found." $RED
    exit 1
fi

print_status "✅ Widget built successfully!" $GREEN
echo ""

# Go back to project root
cd ..

# Check backend dependencies
print_status "🔍 Checking backend requirements..." $BLUE
if ! command -v python &> /dev/null; then
    print_status "❌ Python not found! Please install Python 3.8+." $RED
    exit 1
fi

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    print_status "🐍 Activating virtual environment..." $YELLOW
    source venv/bin/activate
elif [ -d ".venv" ]; then
    print_status "🐍 Activating virtual environment..." $YELLOW
    source .venv/bin/activate
else
    print_status "⚠️ No virtual environment found. Using system Python." $YELLOW
fi

# Install backend dependencies if needed
if [ ! -f "requirements_installed.marker" ]; then
    print_status "📥 Installing backend dependencies..." $YELLOW
    pip install -r requirements.txt
    touch requirements_installed.marker
    print_status "✅ Backend dependencies installed!" $GREEN
fi

# Start the FastAPI backend
print_status "🚀 Starting FastAPI Backend (port 5050)..." $BLUE
python src/main.py &
BACKEND_PID=$!
echo $BACKEND_PID > .backend_pid
print_status "Backend PID: $BACKEND_PID" $CYAN

# Start the file server for static content
print_status "🌐 Starting Static File Server (port 8080)..." $BLUE
python -m http.server 8080 &
FILESERVER_PID=$!
echo $FILESERVER_PID > .fileserver_pid
print_status "File Server PID: $FILESERVER_PID" $CYAN

echo ""
print_status "⏳ Waiting for services to initialize..." $YELLOW
print_status "   (Backend needs time to load AI models...)" $YELLOW

# Wait up to 60 seconds for backend to be ready
print_status "🔄 Testing backend connection..." $BLUE
for i in {1..60}; do
    if curl -s http://localhost:5050/api/health > /dev/null 2>&1; then
        print_status "✅ Backend API is healthy! (Ready in ${i}s)" $GREEN
        BACKEND_READY=true
        break
    fi
    if [ $i -eq 60 ]; then
        print_status "❌ Backend failed to start after 60s. Check the logs:" $RED
        print_status "   tail -f backend.log" $YELLOW
        kill $FILESERVER_PID 2>/dev/null || true
        exit 1
    fi
    echo -n "."
    sleep 1
done

echo ""

# Check if file server is running
print_status "🔄 Testing file server..." $BLUE
if curl -s http://localhost:8080 > /dev/null 2>&1; then
    print_status "✅ File server is running!" $GREEN
else
    print_status "❌ File server failed to start." $RED
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Check if widget file exists and is accessible
print_status "🔄 Testing widget accessibility..." $BLUE
if curl -s http://localhost:8080/react-egypt-chatbot-widget/build/egypt-tourism-widget.min.js > /dev/null 2>&1; then
    print_status "✅ Widget is accessible!" $GREEN
else
    print_status "⚠️ Widget may not be accessible at expected URL." $YELLOW
fi

echo ""
print_status "🎉 KARIM'S WEBSITE IS READY!" $GREEN
print_status "============================" $GREEN
echo ""
print_status "🔗 Demo Website: http://localhost:8080/karim-website-demo.html" $CYAN
print_status "🔧 Backend API: http://localhost:5050/api/health" $CYAN
print_status "📁 File Server: http://localhost:8080/" $CYAN
echo ""

# Test the complete integration
print_status "🧪 Running integration tests..." $BLUE

# Test backend health
if curl -s http://localhost:5050/api/health | grep -q "healthy\|ok\|ready"; then
    print_status "✅ Backend health check passed" $GREEN
else
    print_status "⚠️ Backend health check unclear" $YELLOW
fi

# Test CORS configuration
if curl -s -H "Origin: http://localhost:8080" -I http://localhost:5050/api/health | grep -q "Access-Control-Allow-Origin"; then
    print_status "✅ CORS configuration working" $GREEN
else
    print_status "⚠️ CORS headers may need attention" $YELLOW
fi

# Test widget file
WIDGET_SIZE=$(curl -s http://localhost:8080/react-egypt-chatbot-widget/build/egypt-tourism-widget.min.js | wc -c)
if [ $WIDGET_SIZE -gt 1000 ]; then
    print_status "✅ Widget file looks good (${WIDGET_SIZE} bytes)" $GREEN
else
    print_status "⚠️ Widget file may be incomplete (${WIDGET_SIZE} bytes)" $YELLOW
fi

echo ""
print_status "🌐 Opening Karim's Website in your default browser..." $PURPLE

# Open the demo website
if command -v open &> /dev/null; then
    # macOS
    open http://localhost:8080/karim-website-demo.html
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open http://localhost:8080/karim-website-demo.html
elif command -v start &> /dev/null; then
    # Windows
    start http://localhost:8080/karim-website-demo.html
else
    print_status "🔗 Please open: http://localhost:8080/karim-website-demo.html" $CYAN
fi

echo ""
print_status "📋 WHAT TO EXPECT:" $PURPLE
print_status "==================" $PURPLE
print_status "✨ Beautiful gradient background with floating particles" $CYAN
print_status "💬 Chat widget in bottom-right corner" $CYAN
print_status "🤖 AI responses from your Egypt Tourism Chatbot" $CYAN
print_status "🎨 'Karim's Website' title with animated effects" $CYAN
echo ""

print_status "🛑 TO STOP ALL SERVICES:" $YELLOW
print_status "========================" $YELLOW
print_status "Press Ctrl+C in this terminal, or run:" $YELLOW
print_status "kill $BACKEND_PID $FILESERVER_PID" $YELLOW
echo ""

print_status "🎊 ENJOY YOUR DEMO!" $PURPLE

# Create shutdown function
cleanup() {
    echo ""
    print_status "🛑 Shutting down Karim's Website Demo..." $YELLOW
    kill $BACKEND_PID 2>/dev/null || true
    kill $FILESERVER_PID 2>/dev/null || true
    rm -f .backend_pid .fileserver_pid 2>/dev/null || true
    print_status "✅ All services stopped. Goodbye!" $GREEN
    exit 0
}

# Set up signal handlers
trap cleanup INT TERM

# Keep script running and show live status
while true; do
    sleep 30
    
    # Check if services are still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_status "❌ Backend process died unexpectedly!" $RED
        cleanup
    fi
    
    if ! kill -0 $FILESERVER_PID 2>/dev/null; then
        print_status "❌ File server process died unexpectedly!" $RED
        cleanup
    fi
    
    # Optional: Show a heartbeat
    print_status "💓 Services running... (Backend: $BACKEND_PID, File Server: $FILESERVER_PID)" $CYAN
done 