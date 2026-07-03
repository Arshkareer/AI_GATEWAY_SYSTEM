@echo off
echo 🚀 Setting up AI Gateway Monitoring Platform...

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.11+
    pause
    exit /b 1
)

echo ✅ Python detected

:: Create virtual environment
echo 📦 Creating virtual environment...
cd backend
python -m venv venv

:: Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

:: Install dependencies
echo 📥 Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

:: Copy environment file
if not exist .env (
    echo ⚙️ Creating .env file...
    copy .env.example .env
    echo 📝 Please edit .env file with your configuration
)

:: Check if Docker is available
docker --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Docker not found. Please install Docker or setup PostgreSQL and Redis manually
) else (
    echo 🐳 Docker detected. You can use 'docker-compose up -d' to start services
)

echo.
echo 🎉 Setup completed!
echo.
echo Next steps:
echo 1. Edit backend\.env with your database and API keys
echo 2. Start services: docker-compose up -d
echo 3. Run migrations: cd backend ^&^& alembic upgrade head
echo 4. Start backend: cd backend ^&^& uvicorn app.main:app --reload
echo 5. Visit http://localhost:8000/docs for API documentation
echo.
echo Happy coding! 🚀
pause