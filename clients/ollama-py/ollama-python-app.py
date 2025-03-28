import requests
import json
import sys
from typing import List, Dict, Any, Optional
import asyncio

from mcp_client import MCPClient

class OllamaClient:
    """Cliente sencillo para interactuar con la API de Ollama"""
    
    def __init__(self, base_url="http://localhost:11434"):
        """
        Inicializa el cliente de Ollama
        
        Args:
            base_url (str): URL base de la API de Ollama
        """
        self.base_url = base_url
        self.clientMCP = MCPClient(
            command="node",
            args=["/Users/alexyslozada/github.com/alexyslozada/mcp-course/servers/basic/dist/server.js"]
        )
        self.toolsMCP = None
        # Verificar si Ollama está funcionando
        try:
            self.check_connection()
            print("✅ Conexión establecida con Ollama")
        except Exception as e:
            print(f"❌ Error al conectarse a Ollama: {e}")
            print("Asegúrate de que Ollama esté instalado y ejecutándose")
            sys.exit(1)

    async def __aenter__(self):
        """Async context manager entry"""
        await self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.clientMCP:
            await self.clientMCP.__aexit__(exc_type, exc_val, exc_tb)

    async def setup(self):
        """Configura las herramientas MCP de manera asíncrona"""
        try:
            if self.clientMCP:
                await self.clientMCP.__aenter__()
                self.toolsMCP = await self.clientMCP.list_tools()
                print("✅ Conexión establecida con servidor MCP")
        except Exception as e:
            print(f"❌ Error al conectarse al servidor MCP: {e}")
            self.toolsMCP = None
    
    def check_connection(self):
        """Verifica la conexión con Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                raise Exception(f"Error al conectarse: {response.status_code}")
            return True
        except requests.exceptions.ConnectionError:
            raise Exception("No se pudo conectar al servidor de Ollama")
    
    def list_models(self):
        """
        Lista todos los modelos disponibles en Ollama
        
        Returns:
            list: Lista de modelos disponibles
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                return response.json().get("models", [])
            else:
                print(f"Error al obtener modelos: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error al listar modelos: {e}")
            return []

    async def execute_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """
        Ejecuta una herramienta MCP
        
        Args:
            tool_name (str): Nombre de la herramienta
            arguments (dict): Argumentos para la herramienta
            
        Returns:
            Any: Resultado de la ejecución de la herramienta
        """
        if not self.clientMCP or not self.toolsMCP:
            raise RuntimeError("MCP Client not connected or tools not available")
        
        try:
            result = await self.clientMCP.execute_tool(tool_name, arguments)
            return result
        except Exception as e:
            print(f"Error executing MCP tool {tool_name}: {e}")
            raise

    def chat(self, model: str, messages: List[Dict[str, str]], options: Optional[Dict[str, Any]] = None):
        """
        Realiza una conversación con el modelo
        
        Args:
            model (str): Nombre del modelo a utilizar
            messages (list): Lista de mensajes en formato [{role: str, content: str}]
            options (dict): Opciones adicionales para la conversación
            
        Returns:
            str: Respuesta generada por el modelo o dict con llamada a función
        """
        # Definir las tools que el modelo puede llamar
        tools = [
            {
                'type': 'function',
                'function': {
                    'name': 'get_current_weather',
                    'description': 'Get the current weather for a city',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'city': {
                                'type': 'string',
                                'description': 'The name of the city',
                            },
                        },
                        'required': ['city'],
                    },
                },
            },
            {
                'type': 'function',
                'function': {
                    'name': 'sum_two_numbers',
                    'description': 'Sum two numbers together',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'number_a': {
                                'type': 'number',
                                'description': 'First number to add',
                            },
                            'number_b': {
                                'type': 'number',
                                'description': 'Second number to add',
                            },
                        },
                        'required': ['number_a', 'number_b'],
                    },
                },
            },
        ]

        # Agregar herramientas MCP si están disponibles
        if self.toolsMCP and hasattr(self.toolsMCP, 'tools'):
            for mcp_tool in self.toolsMCP.tools:
                # Convertir herramientas MCP al formato de herramientas de Ollama
                # Esto es una simplificación - puede necesitar adaptarse según la estructura exacta
                tools.append({
                    'type': 'function',
                    'function': {
                        'name': f"mcp_{mcp_tool.name}",
                        'description': mcp_tool.description if hasattr(mcp_tool, 'description') else f"MCP tool: {mcp_tool.name}",
                        'parameters': mcp_tool.inputSchema if hasattr(mcp_tool, 'inputSchema') else {'type': 'object'}
                    }
                })
        
        print("Tools finales:")
        print(json.dumps(tools, indent=2))
        print("="*100)

        data = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "stream": False
        }
        
        if options:
            data.update(options)
        
        try:
            response = requests.post(f"{self.base_url}/api/chat", json=data, timeout=60)
            if response.status_code != 200:
                print(f"Error en la conversación: {response.status_code}")
                print(f"Respuesta: {json.dumps(response.json(), indent=2)}")
                return None

            # Procesar la respuesta
            lines = response.text.strip().split('\n')
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
                        # No seguimos acumulando respuesta si hay una llamada a función
                        break
                    
                    # Si no es una llamada a función, acumular la respuesta normal
                    if "message" in resp_json and "content" in resp_json["message"]:
                        content = resp_json["message"].get("content")
                        if content:  # Evitar None
                            full_response += content
                        
                except json.JSONDecodeError:
                    print(f"Error al decodificar la respuesta: {line}")
                    continue
            
            return full_response
        except Exception as e:
            print(f"Error al chatear: {e}")
            return None


async def process_function_call(model_name: str, response: dict, messages: list, client: OllamaClient):
    """
    Procesa una llamada a función del modelo y maneja la respuesta
    
    Args:
        model_name (str): Nombre del modelo
        response (dict): Respuesta del modelo con la llamada a función
        messages (list): Historial de mensajes
        client (OllamaClient): Cliente de Ollama
    """
    try:
        function_call = response["function_call"]
        function_name = function_call["function"]["name"]
        
        # Intentar parsear los argumentos como JSON
        try:
            function_args_str = function_call["function"]["arguments"]
            print(f"Arguments: {function_args_str}")
            function_args = function_args_str if isinstance(function_args_str, dict) else json.loads(function_args_str)
        except json.JSONDecodeError:
            print(f"Error decodificando argumentos JSON: {function_args_str}")
            function_args = {}
        
        # Generar un ID único para la llamada a función
        function_call_id = "call_" + str(len(messages))
        
        print(f"\n{model_name} quiere llamar a la función: {function_name}")
        print(f"Con los argumentos: {json.dumps(function_args, indent=2)}")
        
        # Ejecutar la función correspondiente
        function_result = await execute_function(function_name, function_args, client)
        if function_result is None:
            print(f"Error: Función {function_name} no implementada")
            function_result = "Error: Función no implementada o falló la ejecución"
        
        print(f"Resultado: {function_result}")
        
        # Agregar el resultado de la función al historial de mensajes
        messages.append({
            "role": "assistant", 
            "content": None,
            "tool_calls": [
                {
                    "id": function_call_id,  # Importante: incluir el ID
                    "function": {
                        "name": function_name,
                        "arguments": function_args_str
                    }
                }
            ]
        })
        
        # Agregar el resultado de la función
        messages.append({
            "role": "tool",
            "tool_call_id": function_call_id,
            "name": function_name,
            "content": function_result
        })
        
        # Obtener la respuesta final del modelo después de la llamada a función
        print("Obteniendo respuesta final después de la llamada a la función...")
        final_response = client.chat(model_name, messages)
        if isinstance(final_response, dict) and final_response.get("type") == "function_call":
            # Si hay otra llamada a función, procesarla recursivamente
            await process_function_call(model_name, final_response, messages, client)
        elif isinstance(final_response, str):
            print(f"\n{model_name}: {final_response}")
            messages.append({"role": "assistant", "content": final_response})
        else:
            print("No se pudo obtener una respuesta final del modelo")
    except Exception as e:
        print(f"Error procesando la llamada a función: {e}")
        import traceback
        traceback.print_exc()

async def execute_function(function_name: str, function_args: dict, client: OllamaClient) -> Optional[str]:
    """
    Ejecuta una función específica con sus argumentos
    
    Args:
        function_name (str): Nombre de la función a ejecutar
        function_args (dict): Argumentos de la función
        client (OllamaClient): Cliente de Ollama (para acceso a MCP)
    
    Returns:
        Optional[str]: Resultado de la función o None si hay error
    """
    try:
        # Comprobar si es una herramienta MCP
        if function_name.startswith("mcp_"):
            # Extraer el nombre real de la herramienta sin el prefijo mcp_
            actual_tool_name = function_name[4:]
            try:
                # Ejecutar la herramienta MCP
                print(f"Ejecutando herramienta MCP: {actual_tool_name}")
                result = await client.execute_mcp_tool(actual_tool_name, function_args)
                print(f"Resultado: {result}")
                return str(result)
            except Exception as e:
                return f"Error ejecutando la herramienta MCP {actual_tool_name}: {e}"
        
        # Funciones predefinidas
        if function_name == "get_current_weather":
            city = function_args.get("city", "")
            if not city:
                return "Error: Ciudad no especificada"
            return f"El clima en {city} es soleado con 25°C"
            
        elif function_name == "sum_two_numbers":
            try:
                number_a = float(function_args.get("number_a", 0))
                number_b = float(function_args.get("number_b", 0))
                sum_result = number_a + number_b
                return f"La suma de {number_a} y {number_b} es {sum_result}"
            except ValueError:
                return "Error: Los argumentos deben ser números"
        
        return f"Función {function_name} no implementada"
    except Exception as e:
        print(f"Error ejecutando la función {function_name}: {e}")
        import traceback
        traceback.print_exc()
        return f"Error ejecutando la función: {e}"

async def interactive_chat(client: OllamaClient):
    """Modo chat interactivo con Ollama"""
    model_name = "mistral:latest"
    
    # Verificar si el modelo existe
    models = client.list_models()
    model_exists = any(model["name"] == model_name for model in models)
    if not model_exists:
        print(f"El modelo '{model_name}' no está disponible localmente.")
        print("Modelos disponibles:")
        for model in models:
            print(f" - {model['name']}")
        
        # Usar el primer modelo disponible si hay alguno
        if models:
            model_name = models[0]["name"]
            print(f"Usando el modelo: {model_name}")
        else:
            print("No hay modelos disponibles. Saliendo.")
            return
    
    # Iniciar chat
    messages = []
    messages.append({
        "role": "system", 
        "content": "Eres un agente que consultará las tools que están disponibles en la conversación",
    })
    
    print("\nIniciando chat (escribe '/salir' para terminar)")
    while True:
        try:
            user_message = input("\nTú: ")
            
            if user_message.lower() in ["/salir", "/exit", "/quit"]:
                break
            
            messages.append({"role": "user", "content": user_message})
            
            print("Generando respuesta...")
            response = client.chat(model_name, messages)
            
            if response:
                # Verificar si es una llamada a función
                if isinstance(response, dict) and response.get("type") == "function_call":
                    await process_function_call(model_name, response, messages, client)
                # Si es una respuesta normal (no es llamada a función)
                elif isinstance(response, str):
                    print(f"\n{model_name}: {response}")
                    messages.append({"role": "assistant", "content": response})
                else:
                    print(f"Respuesta en formato desconocido: {response}")
            else:
                print("No se pudo obtener una respuesta del modelo")
        except KeyboardInterrupt:
            print("\nChat interrumpido por el usuario")
            break
        except Exception as e:
            print(f"Error en el chat: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Función principal"""
    async with OllamaClient() as client:
        await interactive_chat(client)

if __name__ == "__main__":
    asyncio.run(main())
