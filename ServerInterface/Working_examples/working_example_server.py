"""External processing server for Home Assistant conversation integration."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import traceback
import sys

app = FastAPI()

class UserInput(BaseModel):
    text: str
    language: str
    conversation_id: Optional[str]
    device_id: Optional[str]

class Command(BaseModel):
    domain: str
    service: str
    data: Dict[str, Any]

class ProcessRequest(BaseModel):
    user_input: UserInput
    states: Dict[str, Any]
    config: Dict[str, Any]

class ErrorDetails(BaseModel):
    message: str
    line_number: int
    file_name: str
    traceback: str

class ProcessResponse(BaseModel):
    response: str
    commands: Optional[List[Command]]
    conversation_id: Optional[str]
    error: Optional[ErrorDetails] = None

def get_error_details() -> ErrorDetails:
    """Extract error details from the current exception."""
    exc_type, exc_value, exc_traceback = sys.exc_info()
    # Get the last frame (where the error occurred)
    tb = traceback.extract_tb(exc_traceback)[-1]
    return ErrorDetails(
        message=str(exc_value),
        line_number=tb.lineno,
        file_name=tb.filename,
        traceback=''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
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
            raise ValueError("This is a test error")
            
        # Simple example processing
        text = request.user_input.text.lower()
        
        if "turn on helix" in text:
            return ProcessResponse(
                response="Turning on Helix light remote",
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
                response="Hello World remote",
                commands=None,
                conversation_id=request.user_input.conversation_id
            )

    except Exception as e:
        error_details = get_error_details()
        return ProcessResponse(
            response="An error occurred",
            commands=None,
            conversation_id=request.user_input.conversation_id,
            error=error_details
        )

if __name__ == "__main__":
    # Allow connections from outside 
    uvicorn.run(
        app, 
        host="0.0.0.0",  # Binds to all network interfaces
        port=8127,
        log_level="info",  # Add logging
        access_log=True    # Enable access logging
    )