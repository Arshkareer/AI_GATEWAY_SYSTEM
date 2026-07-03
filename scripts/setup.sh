#!/bin/bash

# AI Gateway Setup Script

echo "🚀 Setting up AI Gateway Monitoring Platform..."

# Check if Python 3.11+ is installed
python_version=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.11"

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+"
    exit 1
fi

# Check Python version
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $python_version detected. Python 3.11+ is required."
    exit 1
fi

echo "✅ Python $python_version detected"

# Create virtual environment
echo "📦 Creating virtual environment..."
cd backend
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "⚙️ Creating .env file..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration"
fi

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "🐳 Docker detected. You can use 'docker-compose up -d' to start services"
else
    echo "⚠️  Docker not found. Please install Docker or setup PostgreSQL and Redis manually"
fi

echo ""
echo "🎉 Setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your database and API keys"
echo "2. Start services: docker-compose up -d"
echo "3. Run migrations: cd backend && alembic upgrade head"  
echo "4. Start backend: cd backend && uvicorn app.main:app --reload"
echo "5. Visit http://localhost:8000/docs for API documentation"
echo ""
echo "Happy coding! 🚀"