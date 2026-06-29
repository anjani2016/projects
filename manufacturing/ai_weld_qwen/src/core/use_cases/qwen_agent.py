import os
import json
import inspect
import requests
import logging
from typing import List, Callable, Dict, Any

class QwenAgent:
    """
    QwenAgent implements an autonomous agent using Qwen Cloud (DashScope).
    It dynamically inspects Python function signatures to expose them as tools,
    and runs a tool execution loop to answer prompts.
    """
    def __init__(self, model: str = None, tools: List[Callable] = None, system_instructions: str = None):
        self.model = model or os.environ.get("QWEN_MODEL", "qwen-max")
        self.tools = tools or []
        self.system_instructions = system_instructions
        
        # Resolve API Key
        self.api_key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("QWEN_API_KEY")
        
        # DashScope OpenAI-compatible endpoint
        self.endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        
        # Build map of function name -> function reference
        self.tool_map = {func.__name__: func for func in self.tools}
        self.tool_schemas = [self._generate_tool_schema(func) for func in self.tools]

    def _generate_tool_schema(self, func: Callable) -> Dict[str, Any]:
        """Dynamically builds a JSON schema for a Python function."""
        sig = inspect.signature(func)
        doc = func.__doc__ or f"Execute {func.__name__}"
        
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
                
            # Determine parameter type
            py_type = param.annotation
            json_type = "string"
            if py_type == float:
                json_type = "number"
            elif py_type == int:
                json_type = "integer"
            elif py_type == bool:
                json_type = "boolean"
                
            properties[param_name] = {
                "type": json_type,
                "description": f"The parameter '{param_name}' of type {json_type}"
            }
            
            # If no default value, it is required
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
                
        return {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": doc.strip(),
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

    async def chat(self, prompt: str) -> str:
        """Executes a complete reasoning and tool-calling dialogue turn with Qwen."""
        if not self.api_key:
            return "Error during agent execution: DASHSCOPE_API_KEY is not configured in the environment."
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if self.system_instructions:
            messages.append({"role": "system", "content": self.system_instructions})
        messages.append({"role": "user", "content": prompt})
        
        # ReAct loop - maximum 10 iterations to prevent infinite loops
        max_iterations = 10
        for i in range(max_iterations):
            payload = {
                "model": self.model,
                "messages": messages
            }
            if self.tool_schemas:
                payload["tools"] = self.tool_schemas
                payload["tool_choice"] = "auto"
                
            logging.info(f"[QwenAgent] Sending request to {self.model} (Turn {i+1})...")
            try:
                response = requests.post(self.endpoint, headers=headers, json=payload, timeout=60)
                if response.status_code != 200:
                    error_msg = f"API Error {response.status_code}: {response.text}"
                    logging.error(f"[QwenAgent] {error_msg}")
                    return f"Error during agent execution: {error_msg}"
            except Exception as conn_err:
                logging.error(f"[QwenAgent] Connection error: {conn_err}")
                return f"Error during agent execution: Connection failed to Qwen Cloud API."

            resp_json = response.json()
            choice = resp_json.get("choices", [{}])[0]
            message = choice.get("message", {})
            
            # Append Qwen's response to message history
            messages.append(message)
            
            tool_calls = message.get("tool_calls")
            if not tool_calls:
                # No more tool calls, return final response text
                return message.get("content") or ""
                
            # Process tool calls
            for tool_call in tool_calls:
                call_id = tool_call.get("id")
                func_info = tool_call.get("function", {})
                func_name = func_info.get("name")
                func_args_str = func_info.get("arguments", "{}")
                
                try:
                    func_args = json.loads(func_args_str)
                except Exception as json_err:
                    logging.error(f"[QwenAgent] Failed to parse arguments: {func_args_str}. Error: {json_err}")
                    func_args = {}
                    
                logging.info(f"[QwenAgent] Executing tool {func_name} with args: {func_args}")
                
                if func_name in self.tool_map:
                    try:
                        func = self.tool_map[func_name]
                        # Support both async and sync functions in the orchestrator
                        if inspect.iscoroutinefunction(func):
                            result = await func(**func_args)
                        else:
                            result = func(**func_args)
                        
                        tool_output = str(result)
                    except Exception as exec_err:
                        tool_output = f"Error executing tool {func_name}: {exec_err}"
                        logging.error(f"[QwenAgent] {tool_output}")
                else:
                    tool_output = f"Error: Tool '{func_name}' is not registered."
                    logging.error(f"[QwenAgent] {tool_output}")
                    
                # Append tool response
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": func_name,
                    "content": tool_output
                })
                
        return "Error: Maximum agent tool calling iterations exceeded."

class QwenAgentWrapper:
    """Helper wrapper to preserve the context-manager API style of Antigravity Agent."""
    def __init__(self, agent: QwenAgent):
        self.agent = agent
        
    async def __aenter__(self):
        return self.agent
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
