# test_server.py
import requests
import json

# Test data
test_request = {
    "user_input": {
        "text": "Turn on the lights",
        "language": "en",
        "conversation_id": "test123",
        "device_id": None
    },
    "config": {
        "api_key": "test-key",
        "base_url": None,
        "api_version": None,
        "organization": None,
        "options": {
            "chat_model": "gpt-3.5-turbo",
            "max_tokens": 150,
            "top_p": 1.0,
            "temperature": 0.7,
            "functions": [],
            "use_tools": True,
            "context_threshold": 2000,
            "max_function_calls": 3,
            "context_truncate_strategy": "clear"
        }
    },
    "exposed_entities": [],
    "messages": [],
    "chat_summaries": None
}

# Send request
response = requests.post(
    "http://localhost:8012/process",
    json=test_request
)

# Print results
print(f"Status Code: {response.status_code}")
print("Response:")
print(json.dumps(response.json(), indent=2))