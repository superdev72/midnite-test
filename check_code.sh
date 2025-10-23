#!/bin/bash
# Code quality and testing script for Midnite Test

echo "🔍 Running code quality checks..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not activated. Activating..."
    source venv/bin/activate
fi

echo "📝 Running Black formatter..."
black events/ midnite_test/ test_basic.py

echo "🔍 Running Flake8 linter..."
flake8 events/ midnite_test/ test_basic.py

if [ $? -eq 0 ]; then
    echo "✅ All code quality checks passed!"
else
    echo "❌ Code quality issues found. Please fix them."
    exit 1
fi

echo "🧪 Running basic functionality tests..."
python test_basic.py

if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed. Please check the output above."
    exit 1
fi

echo "🎉 All checks completed successfully!"
