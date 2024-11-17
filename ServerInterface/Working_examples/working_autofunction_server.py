# autoFunction_server.py
from fastapi import FastAPI
import uvicorn
from custom_components.extended_openai_conversation.ServerInterface.Helpers.shared_models import *
import traceback
import sys

app = FastAPI()

# Konstante für den Service-Namen
SERVICE_NAME = "auto_function_server"

def get_error_details() -> ErrorDetails:
    """Extract error details from the current exception."""
    exc_type, exc_value, exc_traceback = sys.exc_info()
    tb = traceback.extract_tb(exc_traceback)[-1]
    return ErrorDetails(
        message=str(exc_value),
        line_number=tb.lineno,
        file_name=tb.filename,
        traceback=''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
        service_name=SERVICE_NAME
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/process", response_model=ProcessResponse)
async def process_request(request: ProcessRequest):
    """Process a conversation request."""
    try:
        # Simulate an error for testing
        if "cause error" in request.user_input.text.lower():
            raise ValueError("This is a test error from auto function server")
            
        # Simple example processing
        text = request.user_input.text.lower()
        
        if "turn on helix" in text:
            return ProcessResponse(
                response="Turning on Helix light auto",
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
                response="Hello World auto",
                commands=None,
                conversation_id=request.user_input.conversation_id
            )

    except Exception as e:
        error_details = get_error_details()
        return ProcessResponse(
            response="An error occurred in auto function server",
            commands=None,
            conversation_id=request.user_input.conversation_id,
            error=error_details
        )

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8128,
        log_level="info",
        access_log=True
    )