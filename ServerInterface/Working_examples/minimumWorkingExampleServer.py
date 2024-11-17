# server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import uvicorn

# Initialize FastAPI
app = FastAPI()

# Model Definitions
class UserInput(BaseModel):
    text: str
    language: str
    conversation_id: Optional[str]
    device_id: Optional[str]

class ConfigOptions(BaseModel):
    chat_model: str
    max_tokens: int
    top_p: float
    temperature: float
    functions: List[Dict]
    use_tools: bool
    context_threshold: int
    max_function_calls: int
    context_truncate_strategy: str

class Config(BaseModel):
    api_key: str
    base_url: Optional[str]
    api_version: Optional[str]
    organization: Optional[str]
    options: ConfigOptions

class ProcessRequest(BaseModel):
    user_input: UserInput
    config: Config
    exposed_entities: List[Dict]
    messages: List[Dict]
    chat_summaries: Optional[str]

class ProcessResponse(BaseModel):
    response: str
    messages: Optional[List[Dict]]
    chat_summary: Optional[str]

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "running"}

@app.post("/process")
async def process_conversation(request: ProcessRequest) -> ProcessResponse:
    """Process a conversation request."""
    try:
        # Echo the input as response for testing
        return ProcessResponse(
            response=f"Server received: {request.user_input.text}",
            messages=request.messages,
            chat_summary=request.chat_summaries
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8012)