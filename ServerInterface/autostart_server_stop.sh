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

# Prüfe ob das Script mit sudo-Rechten ausgeführt wird
if [ "$EUID" -ne 0 ]; then
    log "Dieses Script muss mit sudo-Rechten ausgeführt werden!" "${RED}"
    log "Bitte mit 'sudo $0' neu starten" "${YELLOW}"
    exit 1
fi

# Service Name
SERVICE_NAME="conversation-client-server.service"

# Header
log "Stoppe Server Interface..." "${BLUE}"
echo "----------------------------------------"

# 1. Prüfe ob Service läuft
log "Prüfe Service Status..." "${YELLOW}"
if ! systemctl is-active --quiet $SERVICE_NAME; then
    log "Service läuft bereits nicht!" "${YELLOW}"
else
    # Stoppe den Service
    log "Stoppe systemd Service..." "${YELLOW}"
    systemctl stop $SERVICE_NAME
    if [ $? -ne 0 ]; then
        log "Fehler beim Stoppen des Services!" "${RED}"
        systemctl status $SERVICE_NAME
        exit 1
    fi
    log "Service erfolgreich gestoppt" "${GREEN}"
fi

# 2. Suche nach übrigen Python-Prozessen
log "Suche nach übrigen Serverprozessen..." "${YELLOW}"
SERVER_PIDS=$(pgrep -f "server.py")

if [ ! -z "$SERVER_PIDS" ]; then
    log "Gefundene Server-Prozesse: $SERVER_PIDS" "${YELLOW}"
    
    # Versuche zunächst sanft zu beenden
    log "Versuche sanfte Beendigung (SIGTERM)..." "${YELLOW}"
    kill $SERVER_PIDS 2>/dev/null
    
    # Warte kurz
    sleep 2
    
    # Prüfe ob Prozesse noch laufen
    if pgrep -f "server.py" > /dev/null; then
        log "Prozesse reagieren nicht auf SIGTERM" "${RED}"
        log "Erzwinge Beendigung (SIGKILL)..." "${YELLOW}"
        kill -9 $SERVER_PIDS 2>/dev/null
        
        # Prüfe final
        if pgrep -f "server.py" > /dev/null; then
            log "Konnte Prozesse nicht beenden!" "${RED}"
            exit 1
        fi
    fi
    
    log "Alle Server-Prozesse beendet" "${GREEN}"
else
    log "Keine laufenden Server-Prozesse gefunden" "${GREEN}"
fi

# 3. Prüfe Port 8129
log "Prüfe Port 8129..." "${YELLOW}"
if netstat -tuln | grep ":8129 " > /dev/null; then
    log "Port 8129 ist noch belegt!" "${RED}"
    netstat -tuln | grep ":8129 "
    log "Versuche Prozess zu identifizieren..." "${YELLOW}"
    fuser 8129/tcp 2>/dev/null
else
    log "Port 8129 ist frei" "${GREEN}"
fi

# 4. Finale Prüfung
echo "----------------------------------------"
log "Finale Status-Prüfung:" "${YELLOW}"

STATUS_OK=true

# Service Check
if systemctl is-active --quiet $SERVICE_NAME; then
    log "✗ Service läuft noch!" "${RED}"
    STATUS_OK=false
else
    log "✓ Service gestoppt" "${GREEN}"
fi

# Prozess Check
if pgrep -f "server.py" > /dev/null; then
    log "✗ Server-Prozesse laufen noch!" "${RED}"
    STATUS_OK=false
else
    log "✓ Keine Server-Prozesse" "${GREEN}"
fi

# Port Check
if netstat -tuln | grep ":8129 " > /dev/null; then
    log "✗ Port 8129 noch belegt!" "${RED}"
    STATUS_OK=false
else
    log "✓ Port 8129 freigegeben" "${GREEN}"
fi

echo "----------------------------------------"
if [ "$STATUS_OK" = true ]; then
    log "Server wurde erfolgreich gestoppt!" "${GREEN}"
else
    log "Es gibt noch Probleme beim Stoppen des Servers!" "${RED}"
    log "Bitte prüfen Sie die obigen Meldungen" "${YELLOW}"
fi

# Optional: Zeige die letzten Log-Einträge
log "Letzte Log-Einträge:" "${YELLOW}"
journalctl -u $SERVICE_NAME -n 5 --no-pager.s