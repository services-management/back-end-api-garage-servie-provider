#!/bin/bash

# Quick start script for local development

echo "🚀 Starting Fixing Service API..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your database credentials!"
    echo "Press Enter to continue after editing .env file..."
    read
fi

# Start the application
echo "🌟 Starting FastAPI server..."
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔗 API Base URL: http://localhost:8000"
echo ""
uvicorn main:app --reload --host 0.0.0.0 --port 8000

