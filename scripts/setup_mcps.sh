#!/bin/bash
# Setup script for ALPHY MCP servers
# Run this after cloning the repository

set -e

echo "🔧 Setting up ALPHY MCP servers..."
echo ""

# Get the project root (parent of scripts/)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Create mcp-servers directory
mkdir -p mcp-servers

# 1. App Store Scraper MCP (Node.js)
echo "📱 Installing App Store Scraper MCP..."
if [ -d "mcp-servers/mcp-appstore" ]; then
    echo "   Already exists, updating..."
    cd mcp-servers/mcp-appstore
    git pull
    npm install
else
    cd mcp-servers
    git clone https://github.com/appreply-co/mcp-appstore.git
    cd mcp-appstore
    npm install
fi
cd "$PROJECT_ROOT"
echo "   ✅ App Store Scraper MCP installed"
echo ""

# 2. Product Hunt MCP (Python - installed via pip)
echo "📦 Installing Product Hunt MCP..."
uv pip install product-hunt-mcp
echo "   ✅ Product Hunt MCP installed"
echo ""

# 3. Verify installations
echo "🔍 Verifying installations..."
echo ""

# Check App Store MCP
if [ -f "mcp-servers/mcp-appstore/server.js" ]; then
    echo "   ✅ App Store Scraper: mcp-servers/mcp-appstore/server.js"
else
    echo "   ❌ App Store Scraper: NOT FOUND"
fi

# Check Product Hunt MCP
if [ -f ".venv/bin/product-hunt-mcp" ]; then
    echo "   ✅ Product Hunt: .venv/bin/product-hunt-mcp"
else
    echo "   ❌ Product Hunt: NOT FOUND"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Required Environment Variables"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Add these to your .env file:"
echo ""
echo "  # Product Hunt (required)"
echo "  PRODUCT_HUNT_TOKEN=your_token_here"
echo ""
echo "  # Get your token at:"
echo "  # https://www.producthunt.com/v2/oauth/applications"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ MCP setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
