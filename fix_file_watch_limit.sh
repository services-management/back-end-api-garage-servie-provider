#!/bin/bash

# Script to fix "OS file watch limit reached" error on Linux

echo "🔧 Fixing file watch limit for development..."

# Check current limit
CURRENT_LIMIT=$(cat /proc/sys/fs/inotify/max_user_watches 2>/dev/null || echo "unknown")

if [ "$CURRENT_LIMIT" != "unknown" ]; then
    echo "Current limit: $CURRENT_LIMIT"
fi

# Increase the limit (requires sudo)
echo "Increasing file watch limit to 524288..."
echo "This requires sudo privileges."

# Try to increase limit
if sudo sysctl fs.inotify.max_user_watches=524288; then
    echo "✅ File watch limit increased successfully!"
    echo ""
    echo "To make this permanent, add this line to /etc/sysctl.conf:"
    echo "fs.inotify.max_user_watches=524288"
    echo ""
    echo "Or run:"
    echo "echo 'fs.inotify.max_user_watches=524288' | sudo tee -a /etc/sysctl.conf"
    echo "sudo sysctl -p"
else
    echo "❌ Failed to increase limit. You may need to run this script with sudo."
    echo ""
    echo "Alternative: Run the app without auto-reload:"
    echo "  uvicorn main:app --host 0.0.0.0 --port 8000"
fi

