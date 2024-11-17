# server.py
from fastapi import FastAPI
import uvicorn
import httpx
import sys
import os
import traceback

# Füge den Parent-Ordner zum Python Path hinzu
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

# Relativer Import der shared_models
from ServerInterface.Helpers.shared_models import *

app = FastAPI()

# Konstanten
AUTO_FUNCTION_URL = "http://localhost:8128/process"
AUTO_FUNCTION_HEALTH_URL = "http://localhost:8128/health"

def get_error_details(service_name: str = "main_server") -> ErrorDetails:
    """Extract error details from the current exception."""
    exc_type, exc_value, exc_traceback = sys.exc_info()
    tb = traceback.extract_tb(exc_traceback)[-1]
    return ErrorDetails(
        message=str(exc_value),
        line_number=tb.lineno,
        file_name=tb.filename,
        traceback=''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
        service_name=service_name
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        async with httpx.AsyncClient() as client:
            auto_function_health = await client.get(AUTO_FUNCTION_HEALTH_URL)
            if auto_function_health.status_code == 200:
                return {"status": "healthy", "auto_function": "healthy"}
            return {"status": "healthy", "auto_function": "unhealthy"}
    except:
        return {"status": "healthy", "auto_function": "unavailable"}

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
                    # If the AutoFunction service reports an error
                    if auto_function_response.error:
                        return auto_function_response
                    return auto_function_response
        except httpx.HTTPError as e:
            # Could not connect to AutoFunction service
            print(f"Could not connect to AutoFunction service: {e}")
            # Log the error and proceed to local processing
            # Optionally, you can set a flag or add details to the response

        # Fallback to local processing
        text = request.user_input.text.lower()
        
        # Handle both English and German commands
        if "turn on helix" in text or "schalte helix ein" in text:
            return ProcessResponse(
                response="Helix Licht eingeschaltet",
                commands=[
                    Command(
                        domain="light",
                        service="turn_on",
                        data={"entity_id": "light.helix"}
                    )
                ],
                conversation_id=request.user_input.conversation_id
            )
        else:
            return ProcessResponse(
                response="Hallo Welt remote",
                commands=None,
                conversation_id=request.user_input.conversation_id
            )

    except Exception as e:
        error_details = get_error_details()
        # Log the error
        print(f"Error processing request: {e}")
        return ProcessResponse(
            response="An error occurred in main server",
            commands=None,
            conversation_id=request.user_input.conversation_id,
            error=error_details
        )


    except Exception as e:
        error_details = get_error_details()
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