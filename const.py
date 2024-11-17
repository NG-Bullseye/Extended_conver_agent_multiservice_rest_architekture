"""Constants for the Extended Conversation Client integration."""

DOMAIN = "extended_conversation_client"

# Server configuration
CONF_SERVER_URL = "server_url"
# Host IP vom Docker-Host-System verwenden (typisch 172.x.x.x oder host.docker.internal)
DEFAULT_SERVER_URL = "http://172.20.0.1:8129"  # Ersetze mit der tatsächlichen Host-IP
CONF_SERVER_ENABLED = "server_enabled"
DEFAULT_SERVER_ENABLED = True