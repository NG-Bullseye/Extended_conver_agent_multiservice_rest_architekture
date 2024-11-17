# Server Interface Documentation

## Core Architecture

### Base Configuration
```yaml
port: 8129
base_path: /var/lib/docker/volumes/homeassistant_data/_data
python_env: .venv
component_path: custom_components/extended_conversation_client
```

### Directory Structure
```
ServerInterface/
├── Controller/
│   ├── AutoFunctionController
│   ├── SpeechController
│   ├── ConversationController
│   └── FunctionController
├── Services/
│   ├── Autofunction_services/
│   ├── autofunction_spawner_service.py
│   ├── funktion_executer_service.py
│   ├── human_like_response_service.py
│   ├── speech_to_speech_assistant_service.py
│   └── offline_conversation_agent.py
└── server.py
```

## System Configuration

### Service File
Location: `/etc/systemd/system/conversation-client-server.service`

View or edit:
```bash
sudo nano /etc/systemd/system/conversation-client-server.service
```

Content:
```ini
[Unit]
Description=Conversation Client Server Interface
After=network.target

[Service]
Type=simple
User=leona
Group=leona
WorkingDirectory=/var/lib/docker/volumes/homeassistant_data/_data
Environment="PATH=/var/lib/docker/volumes/homeassistant_data/_data/.venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/var/lib/docker/volumes/homeassistant_data/_data"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/var/lib/docker/volumes/homeassistant_data/_data/.venv/bin/python -Xfrozen_modules=off /var/lib/docker/volumes/homeassistant_data/_data/custom_components/extended_conversation_client/ServerInterface/Controller/server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### System Commands
```bash
# View service status
sudo systemctl status conversation-client-server.service

# View logs
sudo journalctl -u conversation-client-server.service -f  # Follow logs
sudo journalctl -u conversation-client-server.service -n 50  # Last 50 lines

# Service control
sudo systemctl start conversation-client-server.service
sudo systemctl stop conversation-client-server.service
sudo systemctl restart conversation-client-server.service

# After modifying service file
sudo systemctl daemon-reload
```

## API Endpoints

### Main Routes
- `POST /process`: Primary conversation processing
- `POST /autofunction/create`: Service creation
- `POST /speech/process`: Speech processing 
- `POST /humanlike/chat`: Human-like responses
- `POST /offline/chat`: Offline processing
- `POST /execute/function`: Function execution

## Dependencies
```python
required_packages = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "openai",
    "speechrecognition",
    "pyttsx3",
    "numpy",
    "tensorflow",
    "transformers",
    "debugpy"  # For debugging support
]
```

## Development Environment

### VS Code Setup

1. Create `.vscode/tasks.json`:
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "▶️ restart Server",
            "type": "shell",
            "command": "echo raspberry | sudo -S /var/lib/docker/volumes/homeassistant_data/_data/custom_components/extended_conversation_client/ServerInterface/autostart_server_restart.sh",
            "group": "build"
        },
        {
            "label": "⏹️ Stop Server",
            "type": "shell",
            "command": "echo raspberry | sudo -S /var/lib/docker/volumes/homeassistant_data/_data/custom_components/extended_conversation_client/ServerInterface/autostart_server_stop.sh",
            "group": "build"
        },
        {
            "label": "ℹ️ Check Server Status",
            "type": "shell",
            "command": "echo raspberry | sudo -S /var/lib/docker/volumes/homeassistant_data/_data/custom_components/extended_conversation_client/ServerInterface/autostart_server_check.sh",
            "group": "test"
        }
    ]
}
```

2. Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Attach to Server",
            "type": "debugpy",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5678
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "/var/lib/docker/volumes/homeassistant_data/_data/custom_components/extended_conversation_client"
                }
            ],
            "justMyCode": false
        }
    ],
    "compounds": [
        {
            "name": "▶️ Restart Server and Debug",
            "configurations": ["Attach to Server"],
            "preLaunchTask": "▶️ restart Server",
            "stopAll": true
        }
    ]
}
```

### Debug Mode Setup

1. Backup current service:
```bash
sudo cp /etc/systemd/system/conversation-client-server.service /etc/systemd/system/conversation-client-server.service.backup
```

2. Enable debug mode:
```bash
sudo nano /etc/systemd/system/conversation-client-server.service
```
Add `-m debugpy --listen 0.0.0.0:5678 --wait-for-client` to ExecStart

3. Install debugpy:
```bash
sudo /var/lib/docker/volumes/homeassistant_data/_data/.venv/bin/pip install debugpy
```

### Integration Testing
```bash
pytest Tests/test_specific_service.py
pytest Tests/  # Full suite
```

## Security Parameters

### Network Security
```yaml
default_bind: localhost
authentication: api_key
rate_limit: True
ssl_enabled: True
```

### Service Isolation
```yaml
isolation:
  environment: True
  error_handling: Independent
  logging: Separate
  resources: Limited
```

## Logging Configuration 
```python
log_config = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/server.log'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file']
    }
}
```