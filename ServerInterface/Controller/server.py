from fastapi import FastAPI, UploadFile, File
import uvicorn
import httpx
import sys
import os
import traceback
from typing import Dict, Type
import voluptuous as vol
import asyncio
from fastapi.responses import JSONResponse
import aiofiles
import tempfile

# Add parent folder to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

# Relative import of shared_models
from ServerInterface.Helpers.shared_models import *

app = FastAPI()

# Constants
AUTO_FUNCTION_URL = "http://localhost:8128/process"
AUTO_FUNCTION_HEALTH_URL = "http://localhost:8128/health"

# Audio Service Constants
AUDIO_SERVICE_URL = "http://audio-service:8130"  # Dummy URL
AUDIO_FORWARD_ENDPOINT = f"{AUDIO_SERVICE_URL}/process_audio"

# Global context to store audio data
AUDIO_CONTEXT = {}

def get_error_details() -> ErrorDetails:
    """Get error details from current exception."""
    exc_type, exc_value, exc_traceback = sys.exc_info()
    return ErrorDetails(
        type=exc_type.__name__ if exc_type else "Unknown",
        message=str(exc_value) if exc_value else "No message",
        traceback=traceback.format_exc()
    )

async def forward_audio_to_service(file_content: bytes, filename: str, conversation_id: str, content_type: str):
    """Forward audio file to the audio processing service."""
    try:
        # Erstelle ein temporäres File für den Multipart Upload
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_content)
            temp_path = temp_file.name

        try:
            # Erstelle den Multipart Form Data
            files = {
                'file': (filename, open(temp_path, 'rb'), content_type)
            }
            data = {
                'conversation_id': conversation_id
            }

            # Sende Request an Audio Service
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    AUDIO_FORWARD_ENDPOINT,
                    files=files,
                    data=data,
                    timeout=30.0
                )

                return {
                    'success': response.status_code == 200,
                    'status_code': response.status_code,
                    'response': response.json() if response.status_code == 200 else None,
                    'error': response.text if response.status_code != 200 else None
                }

        finally:
            # Cleanup: Lösche temporäre Datei
            os.unlink(temp_path)

    except Exception as e:
        print(f"Error forwarding audio: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@app.post("/upload_audio")
async def upload_audio(conversation_id: str, file: UploadFile = File(...)):
    """
    Endpoint to receive audio files and forward them.
    conversation_id: ID to associate the audio with a conversation
    file: The audio file to upload
    """
    try:
        # Read the file content
        content = await file.read()
        
        # Store in context with conversation ID
        AUDIO_CONTEXT[conversation_id] = {
            'filename': file.filename,
            'content': content,
            'content_type': file.content_type,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        # Forward to audio service
        forward_result = await forward_audio_to_service(
            content,
            file.filename,
            conversation_id,
            file.content_type
        )
        
        if not forward_result['success']:
            print(f"Warning: Audio forwarding failed: {forward_result.get('error')}")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Audio uploaded successfully",
                "filename": file.filename,
                "conversation_id": conversation_id,
                "content_type": file.content_type,
                "forward_status": "success" if forward_result.get('success') else "failed",
                "forward_details": forward_result
            }
        )
        
    except Exception as e:
        error_details = get_error_details()
        print(f"Error uploading audio: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "message": "Error uploading audio",
                "error": str(e),
                "details": error_details.dict()
            }
        )

class BaseExecutor:
    def __init__(self, schema: vol.Schema = vol.Schema({})):
        self.schema = schema

    async def validate(self, config: dict) -> bool:
        try:
            self.schema(config)
            return True
        except vol.Error as e:
            raise ValueError(f"Invalid config: {str(e)}")

    async def execute(self, config: dict, context: dict) -> ProcessResponse:
        raise NotImplementedError()

class ResponseExecutor(BaseExecutor):
    def __init__(self):
        super().__init__(
            vol.Schema({
                vol.Required("command"): str,
                vol.Optional("language"): str,
            })
        )
    
    async def execute(self, config: dict, context: dict) -> ProcessResponse:
        """Handle response generation."""
        original_text = context.get("original_text", "")
        response = f"{original_text} remote" if original_text else "remote"
        
        return ProcessResponse(
            response=response,
            commands=None,
            conversation_id=context.get("conversation_id")
        )

class LightControlExecutor(BaseExecutor):
    def __init__(self):
        super().__init__(
            vol.Schema({
                vol.Required("command"): str,
                vol.Optional("entity_id"): str,
                vol.Optional("language"): str,
            })
        )

    async def execute(self, config: dict, context: dict) -> ProcessResponse:
        command = config["command"]
        
        # Erstelle Commands basierend auf dem erkannten Kommando
        commands = None
        if command == "turn_on_helix":
            commands = [
                Command(
                    domain="light",
                    service="turn_on",
                    data={"entity_id": "light.helix"}
                )
            ]

        return ProcessResponse(
            response="",  # Leere Response, da diese vom ResponseExecutor kommt
            commands=commands,
            conversation_id=context.get("conversation_id")
        )

class ExecutorRegistry:
    def __init__(self):
        self._executors: Dict[str, BaseExecutor] = {}

    def register(self, name: str, executor_class: Type[BaseExecutor]):
        """Register a new executor class."""
        self._executors[name] = executor_class()

    def get_executor(self, name: str) -> BaseExecutor:
        """Get an executor instance by name."""
        if name not in self._executors:
            raise ValueError(f"No executor registered for {name}")
        return self._executors[name]

    async def execute_parallel(self, executor_configs: Dict[str, dict], context: dict) -> ProcessResponse:
        """Execute multiple executors in parallel and combine their results."""
        # Erstelle Tasks für jeden Executor
        tasks = []
        for executor_name, config in executor_configs.items():
            executor = self.get_executor(executor_name)
            tasks.append(executor.execute(config, context))
        
        # Führe alle Tasks parallel aus
        results = await asyncio.gather(*tasks)
        
        # Kombiniere die Ergebnisse
        final_commands = []
        final_response = ""
        
        for result in results:
            if result.commands:
                final_commands.extend(result.commands)
            if result.response:
                final_response = result.response  # Nimm die Response vom ResponseExecutor
                
        return ProcessResponse(
            response=final_response,
            commands=final_commands if final_commands else None,
            conversation_id=context.get("conversation_id")
        )

# Create global registry instance
registry = ExecutorRegistry()

# Register executors
registry.register("response", ResponseExecutor)
registry.register("light", LightControlExecutor)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/process", response_model=ProcessResponse)
async def process_request(request: ProcessRequest):
    """Process a conversation request."""
    try:
        # Try the AutoFunction service first
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(AUTO_FUNCTION_URL, json=request.dict())
                if response.status_code == 200:
                    auto_function_response = ProcessResponse(**response.json())
                    if auto_function_response.error:
                        return auto_function_response
                    return auto_function_response
        except httpx.HTTPError as e:
            print(f"Could not connect to AutoFunction service: {e}")

        # Fallback to local processing using executors
        text = request.user_input.text.lower()
        
        # Determine command based on text
        if "turn on helix" in text or "schalte helix ein" in text:
            command = "turn_on_helix"
        else:
            command = "default"
            
        # Execute command
        context = {
            "conversation_id": request.user_input.conversation_id,
            "states": request.states,
            "config": request.config,
            "original_text": request.user_input.text
        }
        
        # Konfiguriere die parallel auszuführenden Executors
        executor_configs = {
            "light": {
                "command": command,
                "entity_id": "light.helix",
                "language": request.user_input.language
            },
            "response": {
                "command": command,
                "language": request.user_input.language
            }
        }
        
        # Führe die Executors parallel aus
        return await registry.execute_parallel(executor_configs, context)

    except Exception as e:
        error_details = get_error_details()
        print(f"Error processing request: {e}")
        return ProcessResponse(
            response="An error occurred in main server",
            commands=None,
            conversation_id=request.user_input.conversation_id,
            error=error_details
        )

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8129,
        log_level="debug",
        access_log=True
    )