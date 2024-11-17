#!/bin/bash

# Farben für die Ausgabe
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging Funktion
log() {
    echo -e "${2}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Service Name
SERVICE_NAME="conversation-client-server.service"


# Header
log "Prüfe Status des Server Interface..." "${BLUE}"
echo "----------------------------------------"

# 1. Systemd Service Status
log "Systemd Service Status:" "${YELLOW}"
if systemctl is-active --quiet $SERVICE_NAME; then
    log "✓ Service läuft" "${GREEN}"
    # Zeige zusätzliche Service-Informationen
    UPTIME=$(systemctl show $SERVICE_NAME --property=ActiveEnterTimestamp | cut -d'=' -f2)
    log "Läuft seit: $UPTIME" "${BLUE}"
else
    log "✗ Service läuft nicht!" "${RED}"
    # Zeige den letzten Fehlerstatus
    log "Letzter Service Status:" "${YELLOW}"
    systemctl status $SERVICE_NAME --no-pager | tail -n 5
fi
echo "----------------------------------------"

# 2. Prozess-Check
log "Prozess-Check:" "${YELLOW}"
if pgrep -f "server.py" > /dev/null; then
    PID=$(pgrep -f "server.py")
    log "✓ Server Prozess gefunden (PID: $PID)" "${GREEN}"
    # Zeige Prozess-Details
    log "Prozess-Details:" "${BLUE}"
    ps -p $PID -o pid,ppid,user,%cpu,%mem,start,time,command
else
    log "✗ Kein Server Prozess gefunden!" "${RED}"
fi
echo "----------------------------------------"

# 3. Port-Check
log "Port-Check (8129):" "${YELLOW}"
if command -v netstat > /dev/null; then
    if netstat -tuln | grep ":8129 " > /dev/null; then
        log "✓ Port 8129 ist aktiv" "${GREEN}"
        # Zeige detaillierte Port-Informationen
        netstat -tuln | grep ":8129 "
    else
        log "✗ Port 8129 ist nicht aktiv!" "${RED}"
    fi
else
    log "netstat nicht verfügbar - Port-Check nicht möglich" "${RED}"
fi
echo "----------------------------------------"

# 4. Log-Check
log "Letzte Log-Einträge:" "${YELLOW}"
if journalctl -u $SERVICE_NAME -n 5 --no-pager > /dev/null 2>&1; then
    journalctl -u $SERVICE_NAME -n 5 --no-pager
else
    log "Keine Logs gefunden oder keine Berechtigung" "${RED}"
fi
echo "----------------------------------------"

# 5. Resource Usage
log "Resource Nutzung:" "${YELLOW}"
if [ ! -z "$PID" ]; then
    CPU=$(ps -p $PID -o %cpu | tail -n 1)
    MEM=$(ps -p $PID -o %mem | tail -n 1)
    log "CPU Nutzung: $CPU%" "${BLUE}"
    log "Memory Nutzung: $MEM%" "${BLUE}"
fi
echo "----------------------------------------"

# Zusammenfassung
log "Zusammenfassung:" "${YELLOW}"
if systemctl is-active --quiet $SERVICE_NAME && pgrep -f "server.py" > /dev/null && netstat -tuln | grep ":8129 " > /dev/null; then
    log "✓ Server läuft normal" "${GREEN}"
else
    log "✗ Server hat Probleme" "${RED}"
    
    # Hilfreiche Hinweise
    log "Mögliche Aktionen:" "${YELLOW}"
    echo -e "${BLUE}1. Server neustarten: ${NC}sudo systemctl restart $SERVICE_NAME"
    echo -e "${BLUE}2. Logs ansehen: ${NC}journalctl -u $SERVICE_NAME -f"
    echo -e "${BLUE}3. Service Status: ${NC}systemctl status $SERVICE_NAME"
fi