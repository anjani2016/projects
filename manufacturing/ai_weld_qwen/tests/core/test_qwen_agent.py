import pytest
from unittest.mock import patch, Mock
from src.core.use_cases.qwen_agent import QwenAgent, QwenAgentWrapper

# Example functions to test schema auto-generation
def dummy_tool_one(path: str) -> str:
    """Analyze a dummy path."""
    return f"Processed {path}"

def dummy_tool_two(value: float, active: bool) -> str:
    """Calculate compliance check."""
    return f"Value: {value}, Status: {active}"

def test_qwen_agent_schema_generation():
    agent = QwenAgent(
        model="qwen-max",
        tools=[dummy_tool_one, dummy_tool_two],
        system_instructions="You are a helper."
    )
    
    assert len(agent.tool_schemas) == 2
    
    # Check dummy_tool_one schema
    schema1 = agent.tool_schemas[0]
    assert schema1["type"] == "function"
    assert schema1["function"]["name"] == "dummy_tool_one"
    assert "path" in schema1["function"]["parameters"]["properties"]
    assert schema1["function"]["parameters"]["properties"]["path"]["type"] == "string"
    assert "path" in schema1["function"]["parameters"]["required"]
    
    # Check dummy_tool_two schema
    schema2 = agent.tool_schemas[1]
    assert schema2["type"] == "function"
    assert schema2["function"]["name"] == "dummy_tool_two"
    assert schema2["function"]["parameters"]["properties"]["value"]["type"] == "number"
    assert schema2["function"]["parameters"]["properties"]["active"]["type"] == "boolean"
    assert "value" in schema2["function"]["parameters"]["required"]
    assert "active" in schema2["function"]["parameters"]["required"]

@pytest.mark.asyncio
@patch("requests.post")
async def test_qwen_agent_react_loop(mock_post):
    # Setup mock API responses
    # First response: returns a tool call to dummy_tool_one
    mock_resp1 = Mock()
    mock_resp1.status_code = 200
    mock_resp1.json.return_value = {
        "choices": [{
            "message": {
                "role": "assistant",
                "tool_calls": [{
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "dummy_tool_one",
                        "arguments": '{"path": "test_path.jpg"}'
                    }
                }]
            }
        }]
    }
    
    # Second response: returns final answer
    mock_resp2 = Mock()
    mock_resp2.status_code = 200
    mock_resp2.json.return_value = {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "STATUS: PASS Everything is clear."
            }
        }]
    }
    
    # Mock post calls in order
    mock_post.side_effect = [mock_resp1, mock_resp2]
    
    agent = QwenAgent(
        model="qwen-max",
        tools=[dummy_tool_one],
        system_instructions="You are a helper."
    )
    # Set mock API key to bypass key presence check
    agent.api_key = "mock-key"
    
    response = await agent.chat("Start inspection")
    
    assert response == "STATUS: PASS Everything is clear."
    # Verify post was called twice
    assert mock_post.call_count == 2
    
    # Verify context manager works
    async with QwenAgentWrapper(agent) as wrapped:
        assert wrapped == agent
