#!/bin/bash

# Farben für die Ausgabe
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
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

# Definiere Pfade
# Ändern in allen Skripten:
SERVICE_NAME="conversation-client-server.service"
SERVER_PATH="/var/lib/docker/volumes/homeassistant_data/_data/custom_components/extended_conversation_client/ServerInterface/Controller"
VENV_PATH="/var/lib/docker/volumes/homeassistant_data/_data/.venv"

# Prüfe ob der Service existiert
if ! systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
    log "Service $SERVICE_NAME wurde nicht gefunden!" "${RED}"
    log "Bitte erst die Service-Datei erstellen und aktivieren." "${YELLOW}"
    exit 1
fi

# Prüfe ob alle benötigten Dateien existieren
if [ ! -f "$SERVER_PATH/server.py" ]; then
    log "server.py wurde nicht gefunden in $SERVER_PATH" "${RED}"
    exit 1
fi

if [ ! -d "$VENV_PATH" ]; then
    log "Virtuelle Umgebung wurde nicht gefunden in $VENV_PATH" "${RED}"
    exit 1
fi

# Stoppe den Service
log "Stoppe laufende Server-Instanz..." "${YELLOW}"
systemctl stop $SERVICE_NAME
if [ $? -ne 0 ]; then
    log "Fehler beim Stoppen des Services!" "${RED}"
    exit 1
fi

# Warte kurz
log "Warte auf Prozess-Ende..." "${YELLOW}"
sleep 2

# Starte den Service neu
log "Starte Server neu..." "${YELLOW}"
systemctl start $SERVICE_NAME
if [ $? -ne 0 ]; then
    log "Fehler beim Starten des Services!" "${RED}"
    systemctl status $SERVICE_NAME
    exit 1
fi

# Warte kurz, damit der Service Zeit hat zu starten
sleep 2

# Prüfe ob der Service erfolgreich gestartet wurde
if systemctl is-active --quiet $SERVICE_NAME; then
    log "Server wurde erfolgreich neu gestartet!" "${GREEN}"
else
    log "Server konnte nicht erfolgreich gestartet werden!" "${RED}"
    log "Zeige Service Status:" "${YELLOW}"
    systemctl status $SERVICE_NAME
    exit 1
fi

# Zeige die letzten Log-Einträge
log "Letzte Log-Einträge:" "${YELLOW}"
journalctl -u $SERVICE_NAME -n 10 --no-pager

# Zeige Port-Status
if command -v netstat > /dev/null; then
    log "Port Status (8129):" "${YELLOW}"
    netstat -tuln | grep 8129 || log "Port 8129 ist nicht aktiv!" "${RED}"
fi

log "Script beendet. Der Server sollte jetzt laufen." "${GREEN}"
log "Für kontinuierliche Log-Überwachung: 'journalctl -u $SERVICE_NAME -f'" "${YELLOW}"