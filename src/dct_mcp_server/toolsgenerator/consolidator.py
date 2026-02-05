"""
Consolidator module for creating parameterized tools from grouped endpoints.

This module takes endpoint definitions with operation grouping (operation|endpoint format)
and generates consolidated tools where multiple operations are combined into a single
parameterized function with an operation_type parameter.
"""

from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class ToolConsolidator:
    """Consolidates multiple endpoint operations into single parameterized tools."""
    
    def __init__(self):
        self.operation_groups: Dict[str, Dict[str, List[str]]] = {}
    
    def parse_endpoint_definitions(self, endpoint_dict: Dict[str, Dict[str, List[str]]]) -> None:
        """Parse endpoint definitions with operation grouping.
        
        Expected format:
        {
            'vdbs': {
                'search': ['/vdbs/search'],
                'provision': ['/vdbs/provision_by_timestamp', '/vdbs/provision_by_snapshot', ...]
                ...
            }
        }
        """
        self.operation_groups = endpoint_dict
        logger.info(f"Parsed {len(endpoint_dict)} tool groups")
    
    def get_consolidated_operations(self, tool_name: str) -> Dict[str, str]:
        """Get all operations for a tool grouped for consolidation.
        
        Returns a dict mapping operation names to their operation_type enum values.
        """
        if tool_name not in self.operation_groups:
            return {}
        
        ops_dict = self.operation_groups[tool_name]
        consolidated = {}
        
        for operation_name in ops_dict.keys():
            # Convert operation name to enum value (UPPERCASE_WITH_UNDERSCORES)
            enum_value = operation_name.upper()
            consolidated[operation_name] = enum_value
        
        return consolidated
    
    def get_endpoints_for_operation(self, tool_name: str, operation_name: str) -> List[str]:
        """Get all endpoint paths for a specific operation."""
        if tool_name not in self.operation_groups:
            return []
        
        ops_dict = self.operation_groups[tool_name]
        if operation_name not in ops_dict:
            return []
        
        return ops_dict[operation_name]
    
    def generate_operation_enum_code(self, tool_name: str) -> str:
        """Generate Python Enum code for operation_type parameter."""
        operations = self.get_consolidated_operations(tool_name)
        if not operations:
            return ""
        
        code = f"""from enum import Enum

class {tool_name.title()}Operation(Enum):
    \"\"\"Available operations for {tool_name} management.\"\"\"
"""
        for op_name, enum_value in sorted(operations.items()):
            code += f'    {enum_value} = "{op_name}"\n'
        
        code += "\n"
        return code
    
    def generate_consolidated_function_signature(
        self, 
        tool_name: str, 
        operation_names: List[str],
        common_params: List[Tuple[str, str]] = None
    ) -> str:
        """Generate function signature for consolidated tool.
        
        Args:
            tool_name: Name of the tool (e.g., 'vdbs')
            operation_names: List of operation names
            common_params: List of (param_name, param_type) tuples for common parameters
        
        Returns:
            Function signature string
        """
        enum_class = f"{tool_name.title()}Operation"
        
        params = [f"operation_type: {enum_class}"]
        
        if common_params:
            for param_name, param_type in common_params:
                params.append(f"{param_name}: {param_type} = None")
        
        signature = f"async def manage_{tool_name}({', '.join(params)}) -> Dict[str, Any]:\n"
        return signature
    
    def generate_operation_routing(
        self, 
        tool_name: str,
        indent: int = 4
    ) -> str:
        """Generate operation routing logic for consolidated function."""
        operations = self.get_consolidated_operations(tool_name)
        enum_class = f"{tool_name.title()}Operation"
        indent_str = " " * indent
        
        code = f'{indent_str}"""Route requests to appropriate endpoint based on operation_type."""\n'
        code += f'{indent_str}operation_map = {{\n'
        
        for op_name in sorted(operations.keys()):
            endpoints = self.get_endpoints_for_operation(tool_name, op_name)
            code += f'{indent_str}    "{op_name}": {endpoints},\n'
        
        code += f'{indent_str}}}\n\n'
        code += f'{indent_str}if operation_type.value not in operation_map:\n'
        code += f'{indent_str}    raise ValueError(f"Unknown operation: {{operation_type.value}}")\n\n'
        code += f'{indent_str}endpoint = operation_map[operation_type.value]\n'
        code += f'{indent_str}return make_api_request(endpoint, ...)\n'
        
        return code
    
    def generate_consolidated_tool(
        self,
        tool_name: str,
        operation_summary_map: Dict[str, str] = None
    ) -> str:
        """Generate complete consolidated tool code.
        
        Args:
            tool_name: Name of the tool
            operation_summary_map: Dict mapping operation names to their descriptions
        
        Returns:
            Complete Python code for consolidated tool
        """
        operations = self.get_consolidated_operations(tool_name)
        enum_class = f"{tool_name.title()}Operation"
        
        code = "from enum import Enum\nfrom typing import Dict, Any, Optional\n\n"
        code += self.generate_operation_enum_code(tool_name)
        
        docstring = f'"""Manage {tool_name} operations through consolidated endpoint.\n'
        
        if operation_summary_map:
            docstring += "\nSupported operations:\n"
            for op_name, summary in sorted(operation_summary_map.items()):
                docstring += f"  - {op_name}: {summary}\n"
        
        docstring += '"""\n'
        
        code += f"@log_tool_execution\n"
        code += f"async def manage_{tool_name}(operation_type: {enum_class}) -> Dict[str, Any]:\n"
        code += f"    {docstring}\n"
        code += self.generate_operation_routing(tool_name)
        
        return code


def consolidate_tools(
    all_operations: Dict[str, Dict[str, List[str]]], 
    max_tools: int = 15
) -> Dict[str, List[str]]:
    """Consolidate operations into a target number of tools.
    
    Args:
        all_operations: Full operation dict from endpoint files
        max_tools: Target maximum number of consolidated tools
    
    Returns:
        Consolidated tool structure
    """
    consolidator = ToolConsolidator()
    consolidator.parse_endpoint_definitions(all_operations)
    
    logger.info(f"Consolidating {len(all_operations)} tools to ≤{max_tools} consolidated tools")
    
    return consolidator.operation_groups
