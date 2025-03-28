from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Optional, Dict, Any

class MCPClient:
    def __init__(self, command: str, args: list[str], env: Optional[Dict[str, str]] = None):
        self.server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env
        )
        self.session = None
        self.read = None
        self.write = None
        self._client_ctx = None
        self._session_ctx = None

    async def connect(self):
        """Establishes connection with the MCP server"""
        try:
            self._client_ctx = stdio_client(self.server_params)
            client = await self._client_ctx.__aenter__()
            self.read, self.write = client
            self._session_ctx = ClientSession(self.read, self.write)
            self.session = await self._session_ctx.__aenter__()
            await self.session.initialize()
            return True
        except Exception as e:
            print(f"Error connecting to MCP server: {e}")
            await self.disconnect()
            return False

    async def disconnect(self):
        """Closes the connection with the MCP server"""
        try:
            if self._session_ctx:
                await self._session_ctx.__aexit__(None, None, None)
                self._session_ctx = None
                self.session = None
            
            if self._client_ctx:
                await self._client_ctx.__aexit__(None, None, None)
                self._client_ctx = None
                self.read = None
                self.write = None
        except Exception as e:
            print(f"Error during disconnect: {e}")

    async def list_tools(self):
        """Lists all available tools from the server"""
        if not self.session:
            raise RuntimeError("Client not connected. Call connect() first")
        try:
            return await self.session.list_tools()
        except Exception as e:
            print(f"Error listing tools: {e}")
            raise

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Executes a specific tool with the given arguments"""
        if not self.session:
            raise RuntimeError("Client not connected. Call connect() first")
        try:
            return await self.session.call_tool(tool_name, arguments)
        except Exception as e:
            print(f"Error executing tool {tool_name}: {e}")
            raise

    async def __aenter__(self):
        success = await self.connect()
        if not success:
            raise RuntimeError("Failed to connect to MCP server")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
