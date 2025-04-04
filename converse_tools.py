from typing import Any, Dict, List, Callable

class ConverseToolManager:
    def __init__(self):
        self._tools = {}

    def register_tool(self, name: str, func: Callable, description: str, input_schema: Dict):
        """
        Register a new tool with the system.
        """
        self._tools[name] = {
            'function': func,
            'description': description,
            'input_schema': input_schema
        }

    def get_tools(self) -> Dict[str, List[Dict]]:
        """
        Generate the tools specification.
        """
        tool_specs = []
        for name, tool in self._tools.items():
            tool_specs.append({
                'toolSpec': {
                    'name': name,  # No more sanitization
                    'description': tool['description'],
                    'inputSchema': tool['input_schema']
                }
            })
        
        return {'tools': tool_specs}

    async def execute_tool(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool based on the agent's request.
        """
        tool_use_id = payload['toolUseId']
        tool_name = payload['product_name']
        tool_input = payload['input']

        if tool_name not in self._tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        try:
            tool_func = self._tools[tool_name]['function']
            result = await tool_func(tool_name, tool_input)
            return {
                'toolUseId': tool_use_id,
                'content': [{'text': str(result)}],
                'status': 'success'
            }
        except Exception as e:
            return {
                'toolUseId': tool_use_id,
                'content': [{'text': f"Error executing tool: {str(e)}"}],
                'status': 'error'
            }

    def clear_tools(self):
        """Clear all registered tools"""
        self._tools.clear()
