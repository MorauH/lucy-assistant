from typing import List, Optional, Dict, Any, Callable, Union
from pydantic import BaseModel, Field, create_model
from langchain.tools import StructuredTool
import httpx
import asyncio
import json
import logging
import subprocess
from dataclasses import dataclass
from enum import Enum
import atexit

logger = logging.getLogger(__name__)

class MCPTransport(str, Enum):
    """MCP transport types"""
    STDIO = "stdio"
    HTTP = "http"

@dataclass
class MCPServer:
    """Configuration for an MCP server"""
    name: str
    transport: MCPTransport
    # For STDIO transport
    command: Optional[List[str]] = None
    args: Optional[List[str]] = None
    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    # For HTTP transport
    base_url: Optional[str] = None
    endpoint: str = "/mcp"  # JSON-RPC endpoint
    # Common settings
    timeout: int = 30

class MCPClient:
    """Standard MCP client supporting STDIO and HTTP transports"""
    
    def __init__(self, servers: List[MCPServer]):
        self.servers = servers
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.stdio_processes: Dict[str, subprocess.Popen] = {}
        self.tools_cache: Dict[str, Dict] = {}
        self.server_capabilities: Dict[str, Dict] = {}
        self.request_id = 0
        self.session_id = None
        self._closed = False
    
    def _next_id(self) -> int:
        """Get next request ID"""
        self.request_id += 1
        return self.request_id
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources"""
        if self._closed:
            return
        
        self._closed = True
        await self.http_client.aclose()
        
        # Terminate STDIO processes
        for name, process in self.stdio_processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        self.stdio_processes.clear()
    
    async def initialize_servers(self) -> None:
        """Initialize all MCP servers"""
        for server in self.servers:
            try:
                await self._initialize_server(server)
            except Exception as e:
                logger.error(f"Failed to initialize server {server.name}: {e}")
    
    async def _initialize_server(self, server: MCPServer) -> None:
        """Initialize a single MCP server"""
        if server.transport == MCPTransport.STDIO:
            await self._initialize_stdio_server(server)
        else:  # HTTP
            await self._initialize_http_server(server)
    
    async def _initialize_stdio_server(self, server: MCPServer) -> None:
        """Initialize a STDIO-based MCP server"""
        if not server.command:
            raise ValueError(f"STDIO server {server.name} requires command")
        
        # Build command
        cmd = server.command.copy()
        if server.args:
            cmd.extend(server.args)
        
        # Start process
        env = server.env.copy() if server.env else {}
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=server.cwd,
            env=env
        )
        
        self.stdio_processes[server.name] = process
        
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "langchain-mcp-client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = await self._stdio_request(server.name, init_request)
        if "error" in response:
            raise Exception(f"MCP initialization error: {response['error']}")
        
        self.server_capabilities[server.name] = response.get("result", {}).get("capabilities", {})
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        await self._stdio_send(server.name, initialized_notification)
    
    async def _initialize_http_server(self, server: MCPServer) -> None:
        """Initialize an HTTP-based MCP server"""
        if not server.base_url:
            raise ValueError(f"HTTP server {server.name} requires base_url")
        
        init_request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "langchain-mcp-client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = await self.http_client.post(
            f"{server.base_url}{server.endpoint}",
            json=init_request,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        result = response.json()
        if "error" in result:
            raise Exception(f"MCP initialization error: {result['error']}")
        
        self.server_capabilities[server.name] = result.get("result", {}).get("capabilities", {})

        self.session_id = response.headers.get("X-Session-ID")
        if not self.session_id:
            raise Exception("MCP initialization error: X-Session-ID not found in response headers")
        print("Acquired session ID:", self.session_id)
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        await self.http_client.post(
            f"{server.base_url}{server.endpoint}",
            json=initialized_notification,
            headers={"Content-Type": "application/json", "X-Session-ID": self.session_id}
        )
    
    async def _stdio_send(self, server_name: str, message: Dict) -> None:
        """Send a message to STDIO server"""
        process = self.stdio_processes.get(server_name)
        if not process:
            raise ValueError(f"STDIO server {server_name} not found or not running")
        
        message_str = json.dumps(message) + '\n'
        process.stdin.write(message_str)
        process.stdin.flush()
    
    async def _stdio_request(self, server_name: str, request: Dict) -> Dict:
        """Send a request to STDIO server and wait for response"""
        process = self.stdio_processes.get(server_name)
        if not process:
            raise ValueError(f"STDIO server {server_name} not found or not running")
        
        request_id = request.get("id")
        await self._stdio_send(server_name, request)
        
        # Read response (this is simplified - real implementation might need buffering)
        while True:
            line = process.stdout.readline()
            if not line:
                raise Exception(f"STDIO server {server_name} closed connection")
            
            try:
                response = json.loads(line.strip())
                # Match response ID for requests, or handle notifications
                if "id" in response and response["id"] == request_id:
                    return response
                elif "method" in response:
                    # This is a notification, could be logged or handled
                    logger.debug(f"Received notification from {server_name}: {response}")
                    continue
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from {server_name}: {line}")
                continue
    
    async def discover_tools(self) -> Dict[str, List[Dict]]:
        """Discover all available tools from all servers"""
        all_tools = {}
    
        for server in self.servers:
            try:
                tools = await self._discover_server_tools(server)
                all_tools[server.name] = tools
                self.tools_cache[server.name] = {tool["name"]: tool for tool in tools}
            except Exception as e:
                logger.error(f"Failed to discover tools from {server.name}: {e}")
                all_tools[server.name] = []
        
        return all_tools
    
    async def _discover_server_tools(self, server: MCPServer) -> List[Dict]:
        """Discover tools from a specific server"""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list"
        }
        
        if server.transport == MCPTransport.STDIO:
            response = await self._stdio_request(server.name, request)
        else:  # HTTP
            http_response = await self.http_client.post(
                f"{server.base_url}{server.endpoint}",
                json=request,
                headers={"Content-Type": "application/json", "X-Session-ID": self.session_id}
            )
            http_response.raise_for_status()
            response = http_response.json()
        
        if "error" in response:
            raise Exception(f"Tools discovery error: {response['error']}")
        
        return response.get("result", {}).get("tools", [])
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a specific tool on a specific server"""
        if self._closed:
            raise Exception("Cannot send a request, as the client has been closed.")
            
        print(f"Calling tool {tool_name} on server {server_name} with arguments {arguments}")
        server = next((s for s in self.servers if s.name == server_name), None)
        if not server:
            print(f"Server {server_name} not found")
            raise ValueError(f"Server {server_name} not found")

        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        if server.transport == MCPTransport.STDIO:
            response = await self._stdio_request(server_name, request)
        else:  # HTTP
            http_response = await self.http_client.post(
                f"{server.base_url}{server.endpoint}",
                json=request,
                headers={"Content-Type": "application/json", "X-Session-ID": self.session_id}
            )
            http_response.raise_for_status()
            response = http_response.json()
        
        if "error" in response:
            raise Exception(f"Tool call error: {response['error']}")
        
        return response.get("result", {})

# Global client instance to keep alive
_global_mcp_client: Optional[MCPClient] = None
_cleanup_registered = False

def _cleanup_global_client():
    """Cleanup function to be called on exit"""
    global _global_mcp_client
    if _global_mcp_client:
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                loop.run_until_complete(_global_mcp_client.cleanup())
        except:
            # If we can't clean up gracefully, that's OK during shutdown
            pass

class MCPToolsManager:
    """Manager for converting MCP tools to LangChain StructuredTools"""
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.langchain_tools: List[StructuredTool] = []
    
    def _create_pydantic_model(self, tool_schema: Dict[str, Any]) -> BaseModel:
        """Create a Pydantic model from MCP tool input schema"""
        if not tool_schema.get("inputSchema"):
            # No input schema, create empty model
            return create_model("EmptyInput")
        
        input_schema = tool_schema["inputSchema"]
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        
        # Convert JSON schema properties to Pydantic fields
        fields = {}
        for prop_name, prop_schema in properties.items():
            field_type = self._json_type_to_python(prop_schema)
            default_value = ... if prop_name in required else None
            fields[prop_name] = (field_type, Field(default=default_value, description=prop_schema.get("description", "")))
        
        return create_model(f"{tool_schema['name']}Input", **fields)
    
    def _json_type_to_python(self, json_schema: Dict[str, Any]) -> type:
        """Convert JSON schema type to Python type"""
        json_type = json_schema.get("type", "string")
        
        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": List[Any],
            "object": Dict[str, Any]
        }
        
        python_type = type_mapping.get(json_type, str)
        
        # Handle optional types
        if json_schema.get("nullable", False) or "null" in json_schema.get("type", []):
            return Optional[python_type]
        
        return python_type
    
    def _create_tool_function(self, server_name: str, tool_name: str):
        """Create a function that calls the MCP tool"""
        async def tool_function(**kwargs):
            try:
                result = await self.mcp_client.call_tool(server_name, tool_name, kwargs)
                # Extract content from MCP response
                if isinstance(result, dict) and "content" in result:
                    content = result["content"]
                    if isinstance(content, list) and len(content) > 0:
                        return content[0].get("text", str(result))
                return str(result)
            except Exception as e:
                return f"Error calling tool {tool_name}: {str(e)}"
        
        # Create sync wrapper with robust event loop handling
        def sync_tool_function(**kwargs):
            import concurrent.futures
            import threading
            
            def run_in_thread():
                # Create a fresh event loop in a new thread
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(tool_function(**kwargs))
                finally:
                    new_loop.close()
            
            # Always use a separate thread to avoid event loop conflicts
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_in_thread)
                return future.result()
        
        return sync_tool_function
    
    async def create_langchain_tools(self) -> List[StructuredTool]:
        """Create LangChain StructuredTools from discovered MCP tools"""
        await self.mcp_client.initialize_servers()
        all_tools = await self.mcp_client.discover_tools()
        
        langchain_tools = []
        
        for server_name, tools in all_tools.items():
            for tool in tools:
                try:
                    # Create Pydantic input model
                    input_model = self._create_pydantic_model(tool)
                    
                    # Create tool function
                    tool_func = self._create_tool_function(server_name, tool["name"])
                    
                    # Create unique tool name to avoid conflicts
                    unique_name = f"{server_name}_{tool['name']}"
                    
                    # Create StructuredTool
                    structured_tool = StructuredTool.from_function(
                        func=tool_func,
                        name=unique_name,
                        description=f"[{server_name}] {tool.get('description', tool['name'])}",
                        args_schema=input_model
                    )
                    
                    langchain_tools.append(structured_tool)
                    logger.info(f"Created LangChain tool: {unique_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to create tool {tool.get('name', 'unknown')} from {server_name}: {e}")
        
        self.langchain_tools = langchain_tools
        return langchain_tools

# Convenience function to get MCP tools for your existing agent
async def get_mcp_tools(server_configs: List[Dict[str, Any]]) -> List[StructuredTool]:
    """
    Get MCP tools as LangChain StructuredTools
    
    Args:
        server_configs: List of server configurations, e.g.:
            [
                # STDIO server
                {
                    "name": "my_stdio_server",
                    "transport": "stdio",
                    "command": ["python", "-m", "my_server"],
                    "args": ["--flag"],
                    "cwd": "/path/to/server",
                    "env": {"VAR": "value"}
                },
                # HTTP server
                {
                    "name": "my_http_server", 
                    "transport": "http",
                    "base_url": "http://localhost:8080",
                    "endpoint": "/mcp"
                }
            ]
    
    Returns:
        List of StructuredTool objects ready for use with LangChain agents
    """
    global _global_mcp_client, _cleanup_registered
    
    # Create server configurations
    servers = []
    for config in server_configs:
        transport = MCPTransport(config["transport"])
        
        server = MCPServer(
            name=config["name"],
            transport=transport,
            command=config.get("command"),
            args=config.get("args"),
            cwd=config.get("cwd"),
            env=config.get("env"),
            base_url=config.get("base_url"),
            endpoint=config.get("endpoint", "/mcp"),
            timeout=config.get("timeout", 30)
        )
        servers.append(server)
    
    # Create and keep alive the MCP client
    _global_mcp_client = MCPClient(servers)
    
    # Register cleanup on exit
    if not _cleanup_registered:
        atexit.register(_cleanup_global_client)
        _cleanup_registered = True
    
    # Create tools manager and return tools
    tools_manager = MCPToolsManager(_global_mcp_client)
    return await tools_manager.create_langchain_tools()

# Example usage function that matches your existing pattern
def get_mcp_tools_sync(server_configs: List[Dict[str, Any]]) -> List[StructuredTool]:
    """
    Synchronous wrapper to get MCP tools
    
    Usage:
        # STDIO server
        stdio_config = {
            "name": "echo_server",
            "transport": "stdio", 
            "command": ["python", "-m", "echo.server"],
            "args": ["--stdio"]
        }
        
        # HTTP server  
        http_config = {
            "name": "vault_server",
            "transport": "http",
            "base_url": "http://localhost:8080",
            "endpoint": "/mcp"
        }
        
        servers = [stdio_config, http_config]
        mcp_tools = get_mcp_tools_sync(servers)
        all_tools = your_existing_tools + mcp_tools
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(get_mcp_tools(server_configs))