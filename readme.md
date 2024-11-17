# ServerInterface Module
on port 8129
## Edit service file for autostart.sh

# anzeigen
sudo cat /etc/systemd/system/autofunction-server.service

# Erstelle das neue Service-File
sudo nano /etc/systemd/system/server-interface.service

# Nachdem du den Inhalt eingefügt hast:
```
sudo systemctl daemon-reload
sudo systemctl enable server-interface.service
sudo systemctl start server-interface.service
```

# hier ändert sich nur der pfad genau wie auch in dem .sh file
```
[Unit]
Description=Server Interface for Extended Conversation Client
After=network.target

[Service]
Type=simple
User=leona
Group=leona
WorkingDirectory=/var/lib/docker/volumes/homeassistant_data/_data/custom_components/extended_conversation_client/ServerInterface
Environment="PATH=/var/lib/docker/volumes/homeassistant_data/_data/.venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/var/lib/docker/volumes/homeassistant_data/_data/.venv"
ExecStart=/var/lib/docker/volumes/homeassistant_data/_data/.venv/bin/python /var/lib/docker/volumes/homeassistant_data/_data/custom_components/extended_conversation_client/ServerInterface/server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```



## Overview
The ServerInterface module serves as a backend for the Home Assistant "Extended OpenAI Conversation" integration. It processes requests from the integration and provides multiple specialized services through a plug-and-play architecture, including AI-powered conversation, speech processing, and dynamic function generation.

## Core Features

### 1. AutoFunction System
- Dynamic service generation and deployment
- Runtime code generation through AI
- Automated testing and deployment pipeline
- Service discovery and integration
- Endpoint: `/autofunction/*`

### 2. Speech-to-Speech Assistant
- Voice input processing
- AI-powered response generation
- Text-to-speech conversion
- Real-time conversation handling
- Endpoint: `/speech/*`

### 3. Human-like Response Service
- Natural language processing
- Context-aware responses
- Personality customization
- Emotion recognition
- Endpoint: `/humanlike/*`

### 4. Offline Conversation Agent
- Local processing capabilities
- Reduced latency
- No internet dependency
- Fallback mechanism
- Endpoint: `/offline/*`

### 5. Function Executor Service
- Distributed function execution
- Remote procedure calls
- Service orchestration
- Error handling
- Endpoint: `/execute/*`

## System Requirements

- Python 3.8 or higher
- Virtual Python environment (venv)
- Systemd-capable Linux system
- Home Assistant installation with "Extended OpenAI Conversation" integration
- Docker (for containerized services)

## Dependencies

### Python Packages
```
fastapi
uvicorn
pydantic
openai
speechrecognition
pyttsx3
numpy
tensorflow
transformers
```

### Integration Dependencies
Required modules from Extended OpenAI Conversation:
```python
from extended_openai_conversation.helpers import set_chat_prompt, get_function_executor
from extended_openai_conversation.const import *
from extended_openai_conversation.exceptions import *
```

## Installation & Setup

### 1. Base Installation
```bash
# Create server directory
mkdir -p /var/lib/docker/volumes/homeassistant_data/_data/custom_components/ServerInterface

# Copy server files
cp -r * /var/lib/docker/volumes/homeassistant_data/_data/custom_components/ServerInterface/

# Setup virtual environment
cd /var/lib/docker/volumes/homeassistant_data/_data
python3 -m venv .venv
source .venv/bin/activate
pip install -r ServerInterface/requirements.txt
```

### 2. Service Configuration

Create system service for each component:

```ini
[Unit]
Description=Extended OpenAI Conversation Server Interface
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=YOUR_USER
Group=YOUR_GROUP
WorkingDirectory=/var/lib/docker/volumes/homeassistant_data/_data/custom_components
Environment="PYTHONPATH=/var/lib/docker/volumes/homeassistant_data/_data/custom_components"
Environment="PATH=/var/lib/docker/volumes/homeassistant_data/_data/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="VIRTUAL_ENV=/var/lib/docker/volumes/homeassistant_data/_data/.venv"
ExecStart=/var/lib/docker/volumes/homeassistant_data/_data/.venv/bin/python3 /var/lib/docker/volumes/homeassistant_data/_data/custom_components/ServerInterface/server.py
Restart=always
RestartSec=1

[Install]
WantedBy=multi-user.target
```

## Service Architecture

### Controllers
Located in `ServerInterface/Controller/`:
- `AutoFunctionController`: Manages dynamic service generation
- `SpeechController`: Handles speech processing
- `ConversationController`: Manages conversation flows
- `FunctionController`: Coordinates function execution

### Services
Located in `ServerInterface/Services/`:
```
Services/
├── Autofunction_services/
│   └── [Dynamically generated services]
├── autofunction_spawner_service.py
├── funktion_executer_service.py
├── human_like_response_service.py
├── speech_to_speech_assistant_service.py
└── offline_conversation_agent.py
```

## API Endpoints

### Main Processing Endpoint
- `POST /process`
  - Handles general conversation processing
  - Integrates with Home Assistant
  - Routes to appropriate service

### Service-Specific Endpoints
- `POST /autofunction/create`: Create new service
- `POST /speech/process`: Process speech input
- `POST /humanlike/chat`: Generate human-like responses
- `POST /offline/chat`: Use offline conversation agent
- `POST /execute/function`: Execute Home Assistant functions

## Management Scripts

### Server Control
```bash
# Restart server
sudo ./custom_components/ServerInterface/autostart_server_restart.sh

# Check status
sudo ./custom_components/ServerInterface/autostart_server_check.sh

# Stop server
sudo ./custom_components/ServerInterface/autostart_server_stop.sh
```

### Service Management
```bash
# Check autofunction status
./check_autofunction.sh

# Restart specific service
./restart_service.sh [service_name]
```

## Plug-and-Play Integration

### Home Assistant Configuration
Add to `configuration.yaml`:
```yaml
extended_openai_conversation:
  server_interface:
    url: "http://localhost:8012"
    services:
      - autofunction
      - speech_to_speech
      - humanlike_response
      - offline_conversation
```

### Service Discovery
1. Services register with the main controller on startup
2. Controller maintains service registry
3. Requests are routed to appropriate service
4. New services can be added without restart

## Security

### Network Security
- Services run on localhost by default
- Configure firewall rules for external access
- API key authentication required
- Rate limiting implemented

### Service Isolation
- Each service runs in isolated environment
- Separate error handling
- Independent logging
- Resource limitations

## Logging and Monitoring

### System Logs
```bash
# View all services
sudo journalctl -u server-interface.service -f

# View specific service
sudo journalctl -u server-interface-[service_name].service -f
```

### Service Logs
Located in `ServerInterface/logs/`:
- `autofunction.log`
- `speech.log`
- `conversation.log`
- `function.log`

## Troubleshooting

### Common Issues
1. Service Discovery Failures
   ```
   Solution: Check service registration and network connectivity
   ```

2. Speech Processing Errors
   ```
   Solution: Verify audio device configuration and dependencies
   ```

3. Offline Mode Issues
   ```
   Solution: Check model availability and system resources
   ```

## Development

### Adding New Services
1. Create service file in `Services/`
2. Implement required interfaces
3. Register with controller
4. Update configuration

### Testing
```bash
# Run test suite
python -m pytest Tests/

# Test specific service
python -m pytest Tests/test_[service_name].py
```

## Contributing
[Add contributing guidelines]

## License
[Specify license]