import requests
import json
import sys
import os
import logging
from enum import Enum
from typing import List, Dict, Any, Optional, Union
import asyncio
from functools import lru_cache

from mcp_client import MCPClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constantes para roles de mensajes
class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

# Configuración
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MCP_SERVER_COMMAND = "node"
DEFAULT_MCP_SERVER_PATH = os.environ.get(
    "MCP_SERVER_PATH", 
    "/Users/alexyslozada/github.com/alexyslozada/mcp-course/servers/basic/dist/server.js"
)
DEFAULT_MODEL = "mistral:latest"

class OllamaAPIClient:
    """Cliente para comunicarse con la API de Ollama"""
    
    def __init__(self, base_url: str = DEFAULT_OLLAMA_URL):
        """
        Inicializa el cliente de la API de Ollama
        
        Args:
            base_url: URL base de la API de Ollama
        """
        self.base_url = base_url

    def check_connection(self) -> bool:
        """
        Verifica la conexión con Ollama
        
        Returns:
            bool: True si la conexión es exitosa
            
        Raises:
            Exception: Si hay un error de conexión
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                raise Exception(f"Error al conectarse: {response.status_code}")
            return True
        except requests.exceptions.ConnectionError:
            raise Exception("No se pudo conectar al servidor de Ollama")
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        Lista todos los modelos disponibles en Ollama
        
        Returns:
            List[Dict[str, Any]]: Lista de modelos disponibles
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                return response.json().get("models", [])
            else:
                logger.error(f"Error al obtener modelos: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error al listar modelos: {e}")
            return []
            
    def chat(
        self, 
        model: str, 
        messages: List[Dict[str, Any]], 
        tools: List[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Union[str, Dict[str, Any]]:
        """
        Envía una solicitud de chat a Ollama
        
        Args:
            model: Nombre del modelo a utilizar
            messages: Lista de mensajes para la conversación
            tools: Lista de herramientas disponibles para el modelo
            options: Opciones adicionales para la API de Ollama
            
        Returns:
            str o dict: Respuesta del modelo o información de llamada a función
        """
        data = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        if tools:
            data["tools"] = tools
            
        if options:
            data.update(options)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat", 
                json=data, 
                timeout=60
            )
            if response.status_code != 200:
                logger.error(f"Error en la conversación: {response.status_code}")
                logger.error(f"Respuesta: {json.dumps(response.json(), indent=2)}")
                return None

            return self._process_response(response.text)
        except Exception as e:
            logger.error(f"Error al chatear: {e}")
            return None
    
    def _process_response(self, response_text: str) -> Union[str, Dict[str, Any]]:
        """
        Procesa la respuesta de texto de la API de Ollama
        
        Args:
            response_text: Texto de respuesta de Ollama
            
        Returns:
            str o dict: Contenido de la respuesta o información de llamada a función
        """
        lines = response_text.strip().split('\n')
        full_response = ""
        
        for line in lines:
            try:
                resp_json = json.loads(line)
                
                # Verificar si hay una llamada a función
                if "message" in resp_json and "tool_calls" in resp_json["message"]:
                    function_call = resp_json["message"]["tool_calls"][0]
                    if function_call:
                        return {
                            "type": "function_call",
                            "function_call": function_call
                        }
                
                # Si no es una llamada a función, acumular la respuesta normal
                if "message" in resp_json and "content" in resp_json["message"]:
                    content = resp_json["message"].get("content")
                    if content:  # Evitar None
                        full_response += content
                    
            except json.JSONDecodeError:
                logger.error(f"Error al decodificar la respuesta: {line}")
                continue
        
        return full_response


class ToolManager:
    """Gestor de herramientas para integrar con modelos de lenguaje"""
    
    def __init__(self):
        """Inicializa el gestor de herramientas con las herramientas integradas"""
        self.built_in_tools = []
    
    def get_all_tools(self, mcp_tools=None) -> List[Dict[str, Any]]:
        """
        Obtiene todas las herramientas disponibles (integradas + MCP)
        
        Args:
            mcp_tools: Herramientas MCP disponibles
            
        Returns:
            List[Dict[str, Any]]: Lista completa de herramientas
        """
        tools = self.built_in_tools.copy()
        
        # Agregar herramientas MCP si están disponibles
        if mcp_tools and hasattr(mcp_tools, 'tools'):
            for mcp_tool in mcp_tools.tools:
                # Convertir herramientas MCP al formato de herramientas de Ollama
                tools.append({
                    'type': 'function',
                    'function': {
                        'name': f"mcp_{mcp_tool.name}",
                        'description': getattr(mcp_tool, 'description', f"MCP tool: {mcp_tool.name}"),
                        'parameters': getattr(mcp_tool, 'inputSchema', {'type': 'object'})
                    }
                })
                
        return tools


class OllamaAgent:
    """Agente que integra Ollama con herramientas MCP y propias"""
    
    def __init__(
        self, 
        ollama_url: str = DEFAULT_OLLAMA_URL,
        mcp_command: str = DEFAULT_MCP_SERVER_COMMAND,
        mcp_args: List[str] = None
    ):
        """
        Inicializa el agente de Ollama
        
        Args:
            ollama_url: URL base de la API de Ollama
            mcp_command: Comando para ejecutar el servidor MCP
            mcp_args: Argumentos para el servidor MCP
        """
        if mcp_args is None:
            mcp_args = [DEFAULT_MCP_SERVER_PATH]
            
        # Inicializar componentes
        self.ollama_client = OllamaAPIClient(ollama_url)
        self.mcp_client = MCPClient(mcp_command, mcp_args)
        self.tool_manager = ToolManager()
        self.toolsMCP = None
        
        # Verificar conexión con Ollama
        try:
            self.ollama_client.check_connection()
            logger.info("✅ Conexión establecida con Ollama")
        except Exception as e:
            logger.error(f"❌ Error al conectarse a Ollama: {e}")
            logger.error("Asegúrate de que Ollama esté instalado y ejecutándose")
            sys.exit(1)

    async def __aenter__(self):
        """Async context manager entry"""
        await self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.mcp_client:
            await self.mcp_client.__aexit__(exc_type, exc_val, exc_tb)

    async def setup(self):
        """Configura el agente y las herramientas MCP"""
        try:
            if self.mcp_client:
                await self.mcp_client.__aenter__()
                self.toolsMCP = await self.mcp_client.list_tools()
                logger.info("✅ Conexión establecida con servidor MCP")
        except Exception as e:
            logger.error(f"❌ Error al conectarse al servidor MCP: {e}")
            self.toolsMCP = None
            
    def list_models(self):
        """Lista todos los modelos disponibles en Ollama"""
        return self.ollama_client.list_models()
    
    async def execute_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """
        Ejecuta una herramienta MCP
        
        Args:
            tool_name: Nombre de la herramienta
            arguments: Argumentos para la herramienta
            
        Returns:
            Any: Resultado de la herramienta
            
        Raises:
            RuntimeError: Si el cliente MCP no está conectado
        """
        if not self.mcp_client or not self.toolsMCP:
            raise RuntimeError("MCP Client not connected or tools not available")
        
        try:
            return await self.mcp_client.execute_tool(tool_name, arguments)
        except Exception as e:
            logger.error(f"Error executing MCP tool {tool_name}: {e}")
            raise

    def chat(self, model: str, messages: List[Dict[str, Any]], options: Optional[Dict[str, Any]] = None):
        """
        Realiza una conversación con el modelo
        
        Args:
            model: Nombre del modelo a utilizar
            messages: Lista de mensajes para la conversación
            options: Opciones adicionales para la API
            
        Returns:
            str o dict: Respuesta del modelo o información de llamada a función
        """
        # Obtener todas las herramientas disponibles
        tools = self.tool_manager.get_all_tools(self.toolsMCP)
        
        # Obtener respuesta del modelo
        return self.ollama_client.chat(model, messages, tools, options)


async def execute_function(function_name: str, function_args: dict, agent: OllamaAgent) -> str:
    """
    Ejecuta una función específica con sus argumentos
    
    Args:
        function_name: Nombre de la función a ejecutar
        function_args: Argumentos de la función
        agent: Agente de Ollama para acceso a herramientas MCP
    
    Returns:
        str: Resultado de la ejecución de la función
    """
    try:
        # Comprobar si es una herramienta MCP
        if function_name.startswith("mcp_"):
            # Extraer el nombre real de la herramienta sin el prefijo mcp_
            actual_tool_name = function_name[4:]
            try:
                logger.info(f"Ejecutando herramienta MCP: {actual_tool_name}")
                result = await agent.execute_mcp_tool(actual_tool_name, function_args)
                logger.info(f"Resultado: {result}")
                return str(result)
            except Exception as e:
                return f"Error ejecutando la herramienta MCP {actual_tool_name}: {e}"
        
        return f"Función {function_name} no implementada"
    except Exception as e:
        logger.error(f"Error ejecutando la función {function_name}: {e}")
        import traceback
        traceback.print_exc()
        return f"Error ejecutando la función: {e}"


async def process_function_call(model_name: str, response: dict, messages: list, agent: OllamaAgent):
    """
    Procesa una llamada a función del modelo y maneja la respuesta
    
    Args:
        model_name: Nombre del modelo
        response: Respuesta del modelo con la llamada a función
        messages: Historial de mensajes
        agent: Agente de Ollama
    """
    try:
        function_call = response["function_call"]
        function_name = function_call["function"]["name"]
        
        # Intentar parsear los argumentos como JSON
        try:
            function_args_str = function_call["function"]["arguments"]
            logger.debug(f"Arguments: {function_args_str}")
            function_args = function_args_str if isinstance(function_args_str, dict) else json.loads(function_args_str)
        except json.JSONDecodeError:
            logger.error(f"Error decodificando argumentos JSON: {function_args_str}")
            function_args = {}
        
        # Generar un ID único para la llamada a función
        function_call_id = "call_" + str(len(messages))
        
        logger.info(f"\n{model_name} quiere llamar a la función: {function_name}")
        logger.info(f"Con los argumentos: {json.dumps(function_args, indent=2)}")
        
        # Ejecutar la función correspondiente
        function_result = await execute_function(function_name, function_args, agent)
        if function_result is None:
            logger.error(f"Error: Función {function_name} no implementada")
            function_result = "Error: Función no implementada o falló la ejecución"
        
        logger.info(f"Resultado: {function_result}")
        
        # Agregar el resultado de la función al historial de mensajes
        messages.append({
            "role": MessageRole.ASSISTANT, 
            "content": None,
            "tool_calls": [
                {
                    "id": function_call_id,
                    "function": {
                        "name": function_name,
                        "arguments": function_args_str
                    }
                }
            ]
        })
        
        # Agregar el resultado de la función
        messages.append({
            "role": MessageRole.TOOL,
            "tool_call_id": function_call_id,
            "name": function_name,
            "content": function_result
        })
        
        # Obtener la respuesta final del modelo después de la llamada a función
        logger.info("Obteniendo respuesta final después de la llamada a la función...")
        final_response = agent.chat(model_name, messages)
        if isinstance(final_response, dict) and final_response.get("type") == "function_call":
            # Si hay otra llamada a función, procesarla recursivamente
            await process_function_call(model_name, final_response, messages, agent)
        elif isinstance(final_response, str):
            print(f"\n{model_name}: {final_response}")
            messages.append({"role": MessageRole.ASSISTANT, "content": final_response})
        else:
            logger.error("No se pudo obtener una respuesta final del modelo")
    except Exception as e:
        logger.error(f"Error procesando la llamada a función: {e}")
        import traceback
        traceback.print_exc()


async def interactive_chat(agent: OllamaAgent):
    """Modo chat interactivo con Ollama"""
    model_name = DEFAULT_MODEL
    
    # Verificar si el modelo existe
    models = agent.list_models()
    model_exists = any(model["name"] == model_name for model in models)
    if not model_exists:
        logger.warning(f"El modelo '{model_name}' no está disponible localmente.")
        logger.info("Modelos disponibles:")
        for model in models:
            logger.info(f" - {model['name']}")
        
        # Usar el primer modelo disponible si hay alguno
        if models:
            model_name = models[0]["name"]
            logger.info(f"Usando el modelo: {model_name}")
        else:
            logger.error("No hay modelos disponibles. Saliendo.")
            return
    
    # Iniciar chat
    messages = []
    messages.append({
        "role": MessageRole.SYSTEM, 
        "content": "Eres un agente que consultará las tools que están disponibles en la conversación",
    })
    
    print("\nIniciando chat (escribe '/salir' para terminar)")
    while True:
        try:
            user_message = input("\nTú: ")
            
            if user_message.lower() in ["/salir", "/exit", "/quit"]:
                break
            
            messages.append({"role": MessageRole.USER, "content": user_message})
            
            print("Generando respuesta...")
            response = agent.chat(model_name, messages)
            
            if response:
                # Verificar si es una llamada a función
                if isinstance(response, dict) and response.get("type") == "function_call":
                    await process_function_call(model_name, response, messages, agent)
                # Si es una respuesta normal (no es llamada a función)
                elif isinstance(response, str):
                    print(f"\n{model_name}: {response}")
                    messages.append({"role": MessageRole.ASSISTANT, "content": response})
                else:
                    logger.error(f"Respuesta en formato desconocido: {response}")
            else:
                logger.error("No se pudo obtener una respuesta del modelo")
        except KeyboardInterrupt:
            print("\nChat interrumpido por el usuario")
            break
        except Exception as e:
            logger.error(f"Error en el chat: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Función principal"""
    async with OllamaAgent() as agent:
        await interactive_chat(agent)


if __name__ == "__main__":
    asyncio.run(main())
