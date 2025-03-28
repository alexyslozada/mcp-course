```mermaid
sequenceDiagram
    participant User
    participant Main
    participant OllamaAgent
    participant OllamaAPIClient
    participant MCPClient
    participant ToolManager

    Note over Main: Program starts
    Main->>OllamaAgent: Create agent
    OllamaAgent->>OllamaAPIClient: Initialize client
    OllamaAgent->>MCPClient: Initialize client
    OllamaAgent->>ToolManager: Initialize manager

    Note over Main: Setup phase
    Main->>OllamaAgent: setup()
    OllamaAgent->>MCPClient: Connect and list tools
    MCPClient-->>OllamaAgent: Return available tools

    Note over Main: Chat loop starts
    loop Interactive Chat
        User->>Main: Input message
        Main->>OllamaAgent: chat(model, messages)
        OllamaAgent->>ToolManager: get_all_tools()
        ToolManager-->>OllamaAgent: Return combined tools (built-in + MCP)
        OllamaAgent->>OllamaAPIClient: chat(model, messages, tools)
        
        alt Normal Response
            OllamaAPIClient-->>OllamaAgent: Return text response
            OllamaAgent-->>Main: Return text response
            Main-->>User: Show response
        else Function Call Response
            OllamaAPIClient-->>OllamaAgent: Return function call
            OllamaAgent-->>Main: Return function call
            Main->>Main: process_function_call()
            
            alt MCP Tool Call
                Main->>OllamaAgent: execute_mcp_tool()
                OllamaAgent->>MCPClient: execute_tool()
                MCPClient-->>OllamaAgent: Return tool result
                OllamaAgent-->>Main: Return result
            end
            
            Main->>OllamaAgent: chat() with tool result
            OllamaAgent-->>Main: Return final response
            Main-->>User: Show final response
        end
    end

    Note over Main: Chat ends when user types '/salir'

# Flujo del Proceso de Chat

Este diagrama de secuencia muestra el flujo completo del proceso de chat en la aplicación. A continuación se explica cada fase:

## 1. Inicialización

- El programa comienza creando una instancia de `OllamaAgent`
- El agente inicializa tres componentes principales:
  - `OllamaAPIClient`: Para comunicación con Ollama
  - `MCPClient`: Para manejar herramientas MCP
  - `ToolManager`: Para gestionar todas las herramientas disponibles

## 2. Fase de Configuración

- Se ejecuta el método `setup()` del agente
- Se establece conexión con el servidor MCP
- Se obtiene la lista de herramientas MCP disponibles

## 3. Bucle de Chat Interactivo

El bucle principal del chat sigue este flujo:

1. El usuario ingresa un mensaje
2. El mensaje se procesa a través del agente
3. El agente:
   - Obtiene todas las herramientas disponibles
   - Envía el mensaje al modelo de Ollama junto con las herramientas

## 4. Procesamiento de Respuestas

La respuesta puede ser de dos tipos:

### Respuesta Normal
- El modelo responde con texto
- La respuesta se muestra directamente al usuario

### Llamada a Función
1. El modelo solicita ejecutar una herramienta
2. Se procesa la llamada a función:
   - Se identifican los argumentos
   - Se ejecuta la herramienta (MCP u otra)
   - Se obtiene el resultado
3. El resultado se envía de vuelta al modelo
4. Se obtiene y muestra la respuesta final

## 5. Finalización

- El chat continúa hasta que el usuario escribe '/salir'
- Se cierran las conexiones y termina el programa

## Notas Importantes

- El sistema maneja un historial de mensajes para mantener el contexto
- Las herramientas MCP se prefijan con "mcp_" para identificarlas
- Todas las respuestas y errores se registran mediante logging
- El sistema puede manejar múltiples llamadas a función en secuencia 