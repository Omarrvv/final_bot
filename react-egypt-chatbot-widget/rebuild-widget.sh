#!/bin/bash

echo "🚀 Rebuilding Egypt Tourism Widget with fixes..."
echo ""

# Change to the widget directory
cd "$(dirname "$0")"

# Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf build/

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Build the widget
echo "🔨 Building widget..."
npm run build

# Check if build was successful
if [ -f "build/widget.js" ]; then
    echo ""
    echo "✅ Widget built successfully!"
    echo "📁 Output: build/widget.js"
    echo ""
    echo "🎯 All fixes applied:"
    echo "  - Removed all flags (using clean EN/AR text)"
    echo "  - Fixed spacing and margins"
    echo "  - Single close button"
    echo "  - Proper scrolling"
    echo "  - Egypt Tourism specific design"
    echo "  - No Qatar references"
    echo ""
    echo "🧪 Test the widget by opening widget-test-fixed.html in your browser"
else
    echo ""
    echo "❌ Build failed! Please check for errors above."
    exit 1
fi 