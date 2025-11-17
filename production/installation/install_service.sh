#!/bin/bash

# Enhanced Trading Bot Service Installation Script
# This script installs the trading bot as a systemd service

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="/Users/homebase/projects/autonomous-trading-ai/production"
SERVICE_FILE="trading-bot.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_FILE"

echo -e "${GREEN}🚀 Installing Enhanced Trading Bot Service${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root (use sudo)${NC}"
    exit 1
fi

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found. Please install Python3 first.${NC}"
    exit 1
fi

# Check if service file exists
if [ ! -f "$PROJECT_DIR/installation/$SERVICE_FILE" ]; then
    echo -e "${RED}❌ Service file not found: $PROJECT_DIR/installation/$SERVICE_FILE${NC}"
    exit 1
fi

# Stop existing service if running
echo -e "${YELLOW}⏹️ Stopping existing service (if running)...${NC}"
systemctl stop trading-bot 2>/dev/null || true

# Copy service file
echo -e "${YELLOW}📋 Installing service file...${NC}"
cp "$PROJECT_DIR/installation/$SERVICE_FILE" "$SERVICE_PATH"

# Set correct permissions
chmod 644 "$SERVICE_PATH"

# Reload systemd
echo -e "${YELLOW}🔄 Reloading systemd...${NC}"
systemctl daemon-reload

# Enable service
echo -e "${YELLOW}✅ Enabling service...${NC}"
systemctl enable trading-bot

# Create log directory
mkdir -p /var/log/trading-bot
chown homebase:homebase /var/log/trading-bot

# Install Python dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
cd "$PROJECT_DIR"
pip3 install -r requirements.txt 2>/dev/null || echo -e "${YELLOW}⚠️ Requirements file not found or failed to install${NC}"

echo -e "${GREEN}✅ Enhanced Trading Bot service installed successfully!${NC}"
echo ""
echo "Available commands:"
echo "  Start service:   sudo systemctl start trading-bot"
echo "  Stop service:    sudo systemctl stop trading-bot"
echo "  Check status:    sudo systemctl status trading-bot"
echo "  View logs:       sudo journalctl -u trading-bot -f"
echo "  Restart service: sudo systemctl restart trading-bot"
echo ""
echo -e "${YELLOW}📝 Note: Configure your bot settings in config.json before starting${NC}"
echo -e "${YELLOW}🔧 Edit the service file at $SERVICE_PATH if you need custom settings${NC}"