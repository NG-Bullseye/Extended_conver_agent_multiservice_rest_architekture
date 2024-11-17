# shared_models.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

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
    service_name: Optional[str] = None

class ProcessResponse(BaseModel):
    response: str
    commands: Optional[List[Command]]
    conversation_id: Optional[str]
    error: Optional[ErrorDetails] = None
