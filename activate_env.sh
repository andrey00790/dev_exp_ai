#!/bin/bash
# Activation script for Hexagonal Architecture environment

echo "🚀 Activating Hexagonal Architecture Environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate

# Verify activation
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment activated: $VIRTUAL_ENV"
else
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

# Check Python version
python_version=$(python --version)
echo "🐍 Python version: $python_version"

# Check if core dependencies are installed
echo "📦 Checking dependencies..."
missing_deps=()

if ! python -c "import fastapi" 2>/dev/null; then
    missing_deps+=("fastapi")
fi

if ! python -c "import uvicorn" 2>/dev/null; then
    missing_deps+=("uvicorn")
fi

if ! python -c "import sqlalchemy" 2>/dev/null; then
    missing_deps+=("sqlalchemy")
fi

if [ ${#missing_deps[@]} -eq 0 ]; then
    echo "✅ All core dependencies available"
else
    echo "⚠️  Missing dependencies: ${missing_deps[*]}"
    echo "💾 Installing missing dependencies..."
    pip install fastapi uvicorn sqlalchemy pydantic bcrypt python-jose pytest httpx python-dotenv
fi

echo ""
echo "🎯 Environment ready! Available commands:"
echo "   python main.py --demo           # Run architecture demo"
echo "   python main.py --reload         # Start development server"
echo "   python demo_hexagonal_architecture.py  # Standalone demo"
echo "   deactivate                      # Exit virtual environment"
echo ""
echo "📚 Documentation:"
echo "   • quick_start_guide.md"
echo "   • ARCHITECTURE_SUCCESS_SUMMARY.md"
echo "" 