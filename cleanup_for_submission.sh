#!/bin/bash
# Cleanup script for Edureka submission

echo "🧹 Cleaning up project for submission..."

# 1. Remove Python cache files
echo "Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete

# 2. Remove macOS system files
echo "Removing macOS system files..."
find . -name ".DS_Store" -delete

# 3. Clear vectorstore (will be regenerated)
echo "Clearing vectorstore..."
rm -rf vectorstore_db/

# 4. Clear uploaded data (admin will upload fresh)
echo "Clearing data/uploads..."
rm -rf data/uploads/orders/*
rm -rf data/uploads/policies/*

# 5. Remove IDE/editor files
echo "Removing IDE files..."
rm -rf .vscode/ .idea/ *.sublime-*

# 6. Create .env.example (don't include actual .env)
echo "Creating .env.example..."
cat > .env.example << 'ENVEOF'
# Groq API Key (required)
# Get your free key from: https://console.groq.com/keys
GROQ_API_KEY=gsk_your_key_here
ENVEOF

echo "✅ Cleanup complete!"
echo ""
echo "Files cleaned:"
echo "  ✓ Python cache (__pycache__, *.pyc)"
echo "  ✓ vectorstore_db/ (2.2MB removed)"
echo "  ✓ data/uploads/ contents"
echo "  ✓ System files (.DS_Store)"
echo ""
echo "Ready for zip creation!"
