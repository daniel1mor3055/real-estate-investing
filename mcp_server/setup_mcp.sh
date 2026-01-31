#!/bin/bash

# Setup script for MCP Ticket Server

echo "=== MCP Ticket Server Setup ==="
echo

# Step 1: Ensure venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

echo

# Step 2: Install dependencies
echo "Installing MCP package..."
echo "Attempting installation with SSL cert handling..."

# Try normal installation first
venv/bin/pip3 install mcp>=1.26.0 2>/dev/null

if [ $? -ne 0 ]; then
    echo "Normal installation failed (SSL issue). Trying with --trusted-host..."
    venv/bin/pip3 install --trusted-host pypi.org --trusted-host files.pythonhosted.org mcp>=1.26.0
    
    if [ $? -ne 0 ]; then
        echo "⚠️  Installation failed. You may need to:"
        echo "   1. Install system certificates: brew install openssl ca-certificates"
        echo "   2. Or manually install: pip3 install --cert /path/to/cert mcp"
        echo "   3. Or upgrade certificates: /Applications/Python*/Install\ Certificates.command"
        exit 1
    fi
fi

echo "✓ MCP package installed successfully"
echo

# Step 3: Verify installation
echo "Verifying installation..."
venv/bin/python3 -c "import mcp; print(f'MCP version: {mcp.__version__}')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✓ MCP import successful"
else
    echo "⚠️  MCP import failed"
    exit 1
fi

echo
echo "=== Setup Complete ==="
echo
echo "Next steps:"
echo "1. Restart Cursor to load the new MCP server"
echo "2. The 'obsidian-tickets' server should appear in your MCP servers list"
echo "3. Use the tools to create tickets in: /Users/danielmo/Desktop/Daniel/Real Estate Project"
