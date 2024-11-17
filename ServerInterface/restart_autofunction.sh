#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${2}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Check if script is run with sudo
if [ "$EUID" -ne 0 ]; then
    log "This script must be run with sudo privileges!" "${RED}"
    log "Please restart with 'sudo $0'" "${YELLOW}"
    exit 1
fi

# Define paths
SERVICE_NAME="autofunction-server.service"
SERVER_PATH="/var/lib/docker/volumes/homeassistant_data/_data/custom_components/extended_openai_conversation/ServerInterface"
VENV_PATH="/var/lib/docker/volumes/homeassistant_data/_data/.venv"
SERVER_SCRIPT="$SERVER_PATH/autofunction_server.py"

# Verbose path checking
log "Checking required paths and files..." "${YELLOW}"

# Check if SERVER_PATH exists
if [ ! -d "$SERVER_PATH" ]; then
    log "Server directory not found: $SERVER_PATH" "${RED}"
    exit 1
else
    log "Server directory found: $SERVER_PATH" "${GREEN}"
fi

# Check if server script exists
if [ ! -f "$SERVER_SCRIPT" ]; then
    log "Server script not found: $SERVER_SCRIPT" "${RED}"
    # List directory contents to help debugging
    log "Contents of $SERVER_PATH:" "${YELLOW}"
    ls -la "$SERVER_PATH"
    exit 1
else
    log "Server script found: $SERVER_SCRIPT" "${GREEN}"
fi

# Check virtual environment
if [ ! -d "$VENV_PATH" ]; then
    log "Virtual environment not found: $VENV_PATH" "${RED}"
    exit 1
else
    log "Virtual environment found: $VENV_PATH" "${GREEN}"
fi

# Check if service exists
if ! systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
    log "Service $SERVICE_NAME not found!" "${RED}"
    log "Please create and enable the service file first." "${YELLOW}"
    exit 1
fi

# Stop the service
log "Stopping running AutoFunction server instance..." "${YELLOW}"
systemctl stop $SERVICE_NAME
if [ $? -ne 0 ]; then
    log "Error stopping the service!" "${RED}"
    systemctl status $SERVICE_NAME
    exit 1
fi

# Wait for process to end
log "Waiting for process to end..." "${YELLOW}"
sleep 2

# Start the service
log "Starting AutoFunction server..." "${YELLOW}"
systemctl start $SERVICE_NAME
if [ $? -ne 0 ]; then
    log "Error starting the service!" "${RED}"
    systemctl status $SERVICE_NAME
    exit 1
fi

# Wait for service to start
sleep 2

# Check if service started successfully
if systemctl is-active --quiet $SERVICE_NAME; then
    log "AutoFunction server restarted successfully!" "${GREEN}"
else
    log "AutoFunction server failed to start!" "${RED}"
    log "Showing service status:" "${YELLOW}"
    systemctl status $SERVICE_NAME
    exit 1
fi

# Show recent logs
log "Recent log entries:" "${YELLOW}"
journalctl -u $SERVICE_NAME -n 10 --no-pager

# Check port status
if command -v netstat > /dev/null; then
    log "Port Status (8128):" "${YELLOW}"
    netstat -tuln | grep 8128 || log "Port 8128 is not active!" "${RED}"
fi

log "Script completed. The AutoFunction server should now be running." "${GREEN}"
log "For continuous log monitoring: 'journalctl -u $SERVICE_NAME -f'" "${YELLOW}"