#!/bin/bash

echo "Starting Project Management System Frontend..."
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
    echo ""
fi

# Run the application
echo "Starting development server at http://localhost:3000"
echo ""
npm run dev

