#!/bin/bash

# Farben für die Ausgabe
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging Funktion
log() {
    printf "${2}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}\n"
}

# Prüfe ob das Script mit sudo-Rechten ausgeführt wird
if [ "$EUID" -ne 0 ]; then
    log "Dieses Script muss mit sudo-Rechten ausgeführt werden!" "${RED}"
    log "Bitte mit 'sudo $0' neu starten" "${YELLOW}"
    exit 1
fi

# Service-Name
SERVICE_NAME="conversation-client-server.service"

# Stoppe den Service
log "Stoppe laufende Server-Instanz..." "${YELLOW}"
systemctl stop $SERVICE_NAME
sleep 2

# Starte den Service neu
log "Starte Server neu..." "${YELLOW}"
systemctl start $SERVICE_NAME
sleep 2

# Zeige Status
if systemctl is-active --quiet $SERVICE_NAME; then
    log "Server wurde erfolgreich neu gestartet!" "${GREEN}"
else
    log "Server konnte nicht erfolgreich gestartet werden!" "${RED}"
    exit 1
fi

# Zeige die letzten Log-Einträge
log "Letzte Log-Einträge:" "${YELLOW}"
journalctl -u $SERVICE_NAME -n 10 --no-pager

log "Script beendet. Der Server sollte jetzt laufen." "${GREEN}"
log "Für kontinuierliche Log-Überwachung: 'journalctl -u $SERVICE_NAME -f'" "${YELLOW}"