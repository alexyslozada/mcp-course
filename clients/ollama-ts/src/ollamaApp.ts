import fetch from 'node-fetch';
import { MCPClient } from './mcpClient.js';

// Configuración de logging
const createLogger = (name: string) => {
  return {
    info: (message: string) => console.log(`[INFO] ${name} - ${message}`),
    error: (message: string) => console.error(`[ERROR] ${name} - ${message}`),
    debug: (message: string) => console.debug(`[DEBUG] ${name} - ${message}`),
    warning: (message: string) => console.warn(`[WARN] ${name} - ${message}`)
  };
};

const logger = createLogger('OllamaApp');

// Constantes para roles de mensajes
enum MessageRole {
  SYSTEM = "system",
  USER = "user",
  ASSISTANT = "assistant",
  TOOL = "tool"
}

// Configuración
const DEFAULT_OLLAMA_URL = "http://localhost:11434";
const DEFAULT_MCP_SERVER_COMMAND = "node";
const DEFAULT_MCP_SERVER_PATH = process.env.MCP_SERVER_PATH ||
  "/Users/alexyslozada/github.com/alexyslozada/mcp-course/servers/basic/dist/server.js";
const DEFAULT_MODEL = "mistral:latest";

// Tipos para TypeScript
interface MessageType {
  role: MessageRole;
  content: string | null;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
  name?: string;
}

interface ToolCall {
  id: string;
  function: {
    name: string;
    arguments: string | Record<string, any>;
  };
}

interface ToolDefinition {
  type: string;
  function: {
    name: string;
    description: string;
    parameters: Record<string, any>;
  };
}

interface OllamaApiOptions {
  temperature?: number;
  top_k?: number;
  top_p?: number;
  num_predict?: number;
  stop?: string[];
  [key: string]: any;
}

/**
 * Cliente para comunicarse con la API de Ollama
 */
class OllamaAPIClient {
  private baseUrl: string;

  /**
   * Inicializa el cliente de la API de Ollama
   * 
   * @param baseUrl URL base de la API de Ollama
   */
  constructor(baseUrl: string = DEFAULT_OLLAMA_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Verifica la conexión con Ollama
   * 
   * @returns True si la conexión es exitosa
   * @throws Error Si hay un error de conexión
   */
  async checkConnection(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/tags`);
      if (response.status !== 200) {
        throw new Error(`Error al conectarse: ${response.status}`);
      }
      return true;
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`No se pudo conectar al servidor de Ollama: ${error.message}`);
      } else {
        throw new Error("No se pudo conectar al servidor de Ollama");
      }
    }
  }

  /**
   * Lista todos los modelos disponibles en Ollama
   * 
   * @returns Lista de modelos disponibles
   */
  async listModels(): Promise<any[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/tags`);
      if (response.status === 200) {
        const data = await response.json() as any;
        return data.models || [];
      } else {
        logger.error(`Error al obtener modelos: ${response.status}`);
        return [];
      }
    } catch (error) {
      logger.error(`Error al listar modelos: ${error}`);
      return [];
    }
  }

  /**
   * Envía una solicitud de chat a Ollama
   * 
   * @param model Nombre del modelo a utilizar
   * @param messages Lista de mensajes para la conversación
   * @param tools Lista de herramientas disponibles para el modelo
   * @param options Opciones adicionales para la API de Ollama
   * @returns Respuesta del modelo o información de llamada a función
   */
  async chat(
    model: string,
    messages: MessageType[],
    tools?: ToolDefinition[],
    options?: OllamaApiOptions
  ): Promise<string | { type: string; function_call: any }> {
    const data: any = {
      model: model,
      messages: messages,
      stream: false
    };

    if (tools) {
      data.tools = tools;
    }

    if (options) {
      Object.assign(data, options);
    }

    try {
      const response = await fetch(
        `${this.baseUrl}/api/chat`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(data),
        }
      );

      if (response.status !== 200) {
        logger.error(`Error en la conversación: ${response.status}`);
        const responseText = await response.text();
        logger.error(`Respuesta: ${responseText}`);
        return "";
      }

      const responseText = await response.text();
      return this._processResponse(responseText);
    } catch (error) {
      logger.error(`Error al chatear: ${error}`);
      return "";
    }
  }

  /**
   * Procesa la respuesta de texto de la API de Ollama
   * 
   * @param responseText Texto de respuesta de Ollama
   * @returns Contenido de la respuesta o información de llamada a función
   */
  private _processResponse(
    responseText: string
  ): string | { type: string; function_call: any } {
    const lines = responseText.trim().split('\n');
    let fullResponse = "";

    for (const line of lines) {
      try {
        const respJson = JSON.parse(line);

        // Verificar si hay una llamada a función
        if (respJson.message && respJson.message.tool_calls) {
          const functionCall = respJson.message.tool_calls[0];
          if (functionCall) {
            return {
              type: "function_call",
              function_call: functionCall
            };
          }
        }

        // Si no es una llamada a función, acumular la respuesta normal
        if (respJson.message && respJson.message.content) {
          const content = respJson.message.content;
          if (content) {
            fullResponse += content;
          }
        }
      } catch (error) {
        logger.error(`Error al decodificar la respuesta: ${line}`);
        continue;
      }
    }

    return fullResponse;
  }
}

/**
 * Gestor de herramientas para integrar con modelos de lenguaje
 */
class ToolManager {
  private builtInTools: ToolDefinition[];

  /**
   * Inicializa el gestor de herramientas con las herramientas integradas
   */
  constructor() {
    this.builtInTools = [];
  }

  /**
   * Obtiene todas las herramientas disponibles 
   * 
   * @param mcpTools Herramientas MCP disponibles
   * @returns Lista completa de herramientas
   */
  getAllTools(mcpTools: any = null): ToolDefinition[] {
    const tools = [...this.builtInTools];

    // Agregar herramientas MCP si están disponibles
    if (mcpTools && mcpTools.tools) {
      for (const mcpTool of mcpTools.tools) {
        // Convertir herramientas MCP al formato de herramientas de Ollama
        tools.push({
          type: 'function',
          function: {
            name: `mcp_${mcpTool.name}`,
            description: mcpTool.description || `MCP tool: ${mcpTool.name}`,
            parameters: mcpTool.inputSchema || { type: 'object' }
          }
        });
      }
    }

    return tools;
  }
}

/**
 * Agente que integra Ollama con herramientas MCP
 */
class OllamaAgent {
  private ollamaClient: OllamaAPIClient;
  private mcpClient: MCPClient;
  private toolManager: ToolManager;
  private toolsMCP: any = null;

  /**
   * Inicializa el agente de Ollama
   * 
   * @param ollamaUrl URL base de la API de Ollama
   * @param mcpCommand Comando para ejecutar el servidor MCP
   * @param mcpArgs Argumentos para el servidor MCP
   */
  constructor(
    ollamaUrl: string = DEFAULT_OLLAMA_URL,
    mcpCommand: string = DEFAULT_MCP_SERVER_COMMAND,
    mcpArgs: string[] = [DEFAULT_MCP_SERVER_PATH]
  ) {
    // Inicializar componentes
    this.ollamaClient = new OllamaAPIClient(ollamaUrl);
    this.mcpClient = new MCPClient(mcpCommand, mcpArgs);
    this.toolManager = new ToolManager();
  }

  /**
   * Configura el agente verificando conexiones
   */
  async setup(): Promise<void> {
    // Verificar conexión con Ollama
    try {
      await this.ollamaClient.checkConnection();
      logger.info("✅ Conexión establecida con Ollama");
    } catch (error) {
      logger.error(`❌ Error al conectarse a Ollama: ${error}`);
      logger.error("Asegúrate de que Ollama esté instalado y ejecutándose");
      process.exit(1);
    }

    // Conectar con el servidor MCP
    try {
      const connected = await this.mcpClient.connect();
      if (connected) {
        this.toolsMCP = await this.mcpClient.listTools();
        logger.info("✅ Conexión establecida con servidor MCP");
      }
    } catch (error) {
      logger.error(`❌ Error al conectarse al servidor MCP: ${error}`);
      this.toolsMCP = null;
    }
  }

  /**
   * Cierra conexiones y limpia recursos
   */
  async cleanup(): Promise<void> {
    await this.mcpClient.disconnect();
  }

  /**
   * Lista todos los modelos disponibles en Ollama
   */
  async listModels(): Promise<any[]> {
    return this.ollamaClient.listModels();
  }

  /**
   * Ejecuta una herramienta MCP
   * 
   * @param toolName Nombre de la herramienta
   * @param arguments Argumentos para la herramienta
   * @returns Resultado de la herramienta
   * @throws Error Si el cliente MCP no está conectado
   */
  async executeMcpTool(toolName: string, args: Record<string, any>): Promise<any> {
    if (!this.mcpClient || !this.toolsMCP) {
      throw new Error("MCP Client not connected or tools not available");
    }

    try {
      return await this.mcpClient.executeTool(toolName, args);
    } catch (error) {
      logger.error(`Error executing MCP tool ${toolName}: ${error}`);
      throw error;
    }
  }

  /**
   * Realiza una conversación con el modelo
   * 
   * @param model Nombre del modelo a utilizar
   * @param messages Lista de mensajes para la conversación
   * @param options Opciones adicionales para la API
   * @returns Respuesta del modelo o información de llamada a función
   */
  async chat(
    model: string,
    messages: MessageType[],
    options?: OllamaApiOptions
  ): Promise<string | { type: string; function_call: any }> {
    // Obtener todas las herramientas disponibles
    const tools = this.toolManager.getAllTools(this.toolsMCP);

    // Obtener respuesta del modelo
    return this.ollamaClient.chat(model, messages, tools, options);
  }
}

/**
 * Ejecuta una función específica con sus argumentos
 * 
 * @param functionName Nombre de la función a ejecutar
 * @param functionArgs Argumentos de la función
 * @param agent Agente de Ollama para acceso a herramientas MCP
 * @returns Resultado de la ejecución de la función
 */
async function executeFunction(
  functionName: string,
  functionArgs: Record<string, any>,
  agent: OllamaAgent
): Promise<string> {
  try {
    // Comprobar si es una herramienta MCP
    if (functionName.startsWith("mcp_")) {
      // Extraer el nombre real de la herramienta sin el prefijo mcp_
      const actualToolName = functionName.substring(4);
      try {
        logger.info(`Ejecutando herramienta MCP: ${actualToolName}`);
        const result = await agent.executeMcpTool(actualToolName, functionArgs);
        logger.info(`Resultado: ${JSON.stringify(result)}`);
        return JSON.stringify(result);
      } catch (error) {
        return `Error ejecutando la herramienta MCP ${actualToolName}: ${error}`;
      }
    }

    return `Función ${functionName} no implementada`;
  } catch (error) {
    logger.error(`Error ejecutando la función ${functionName}: ${error}`);
    console.trace();
    return `Error ejecutando la función: ${error}`;
  }
}

/**
 * Procesa una llamada a función del modelo y maneja la respuesta
 * 
 * @param modelName Nombre del modelo
 * @param response Respuesta del modelo con la llamada a función
 * @param messages Historial de mensajes
 * @param agent Agente de Ollama
 */
async function processFunctionCall(
  modelName: string,
  response: { function_call: any },
  messages: MessageType[],
  agent: OllamaAgent
): Promise<void> {
  try {
    const functionCall = response.function_call;
    const functionName = functionCall.function.name;

    // Intentar parsear los argumentos como JSON
    let functionArgs: Record<string, any> = {};
    try {
      const functionArgsStr = functionCall.function.arguments;
      logger.debug(`Arguments: ${functionArgsStr}`);
      functionArgs = typeof functionArgsStr === 'object'
        ? functionArgsStr
        : JSON.parse(functionArgsStr);
    } catch (error) {
      logger.error(`Error decodificando argumentos JSON: ${functionCall.function.arguments}`);
    }

    // Generar un ID único para la llamada a función
    const functionCallId = "call_" + messages.length;

    logger.info(`\n${modelName} quiere llamar a la función: ${functionName}`);
    logger.info(`Con los argumentos: ${JSON.stringify(functionArgs, null, 2)}`);

    // Ejecutar la función correspondiente
    let functionResult = await executeFunction(functionName, functionArgs, agent);
    if (functionResult === null || functionResult === undefined) {
      logger.error(`Error: Función ${functionName} no implementada`);
      functionResult = "Error: Función no implementada o falló la ejecución";
    }

    logger.info(`Resultado: ${functionResult}`);

    // Agregar el resultado de la función al historial de mensajes
    messages.push({
      role: MessageRole.ASSISTANT,
      content: null,
      tool_calls: [
        {
          id: functionCallId,
          function: {
            name: functionName,
            arguments: typeof functionCall.function.arguments !== 'object'
              ? JSON.stringify(functionCall.function.arguments)
              : functionCall.function.arguments
          }
        }
      ]
    });

    // Agregar el resultado de la función
    messages.push({
      role: MessageRole.TOOL,
      tool_call_id: functionCallId,
      name: functionName,
      content: functionResult
    });

    // Obtener la respuesta final del modelo después de la llamada a función
    logger.info("Obteniendo respuesta final después de la llamada a la función...");
    const finalResponse = await agent.chat(modelName, messages);

    if (typeof finalResponse === 'object' && finalResponse.type === "function_call") {
      // Si hay otra llamada a función, procesarla recursivamente
      await processFunctionCall(modelName, finalResponse, messages, agent);
    } else if (typeof finalResponse === 'string') {
      console.log(`\n${modelName}: ${finalResponse}`);
      messages.push({ role: MessageRole.ASSISTANT, content: finalResponse });
    } else {
      logger.error("No se pudo obtener una respuesta final del modelo");
    }
  } catch (error) {
    logger.error(`Error procesando la llamada a función: ${error}`);
    console.trace();
  }
}

/**
 * Modo chat interactivo con Ollama
 * 
 * @param agent Agente de Ollama configurado
 */
async function interactiveChat(agent: OllamaAgent): Promise<void> {
  let modelName = DEFAULT_MODEL;

  // Verificar si el modelo existe
  const models = await agent.listModels();
  const modelExists = models.some(model => model.name === modelName);

  if (!modelExists) {
    logger.warning(`El modelo '${modelName}' no está disponible localmente.`);
    logger.info("Modelos disponibles:");

    for (const model of models) {
      logger.info(` - ${model.name}`);
    }

    // Usar el primer modelo disponible si hay alguno
    if (models.length > 0) {
      modelName = models[0].name;
      logger.info(`Usando el modelo: ${modelName}`);
    } else {
      logger.error("No hay modelos disponibles. Saliendo.");
      return;
    }
  }

  // Iniciar chat
  const messages: MessageType[] = [];
  messages.push({
    role: MessageRole.SYSTEM,
    content: "Eres un agente que consultará las tools que están disponibles en la conversación",
  });

  console.log("\nIniciando chat (escribe '/salir' para terminar)");

  // Configurar readline para input interactivo
  // Usamos la importación dinámica para ESM
  const readline = (await import('readline')).createInterface({
    input: process.stdin,
    output: process.stdout
  });

  const askQuestion = () => {
    return new Promise<string>((resolve) => {
      readline.question("\nTú: ", (answer: string) => {
        resolve(answer);
      });
    });
  };

  try {
    while (true) {
      const userMessage = await askQuestion();

      if (["/salir", "/exit", "/quit"].includes(userMessage.toLowerCase())) {
        break;
      }

      messages.push({ role: MessageRole.USER, content: userMessage });

      console.log("Generando respuesta...");
      const response = await agent.chat(modelName, messages);

      if (response) {
        // Verificar si es una llamada a función
        if (typeof response === 'object' && response.type === "function_call") {
          await processFunctionCall(modelName, response, messages, agent);
        }
        // Si es una respuesta normal (no es llamada a función)
        else if (typeof response === 'string') {
          console.log(`\n${modelName}: ${response}`);
          messages.push({ role: MessageRole.ASSISTANT, content: response });
        } else {
          logger.error(`Respuesta en formato desconocido: ${response}`);
        }
      } else {
        logger.error("No se pudo obtener una respuesta del modelo");
      }
    }
  } catch (error) {
    logger.error(`Error en el chat: ${error}`);
    console.trace();
  } finally {
    readline.close();
  }
}

/**
 * Función principal
 */
async function main(): Promise<void> {
  const agent = new OllamaAgent();

  try {
    await agent.setup();
    await interactiveChat(agent);
  } finally {
    await agent.cleanup();
  }
}

// Iniciar la aplicación solo si este archivo es el punto de entrada
// En ES modules, usamos import.meta.url para verificar si es el punto de entrada
const isMainModule = import.meta.url === `file://${process.argv[1]}`;
if (isMainModule) {
  main().catch(error => {
    console.error("Error fatal:", error);
    process.exit(1);
  });
}

// Exportamos las clases y funciones para su uso en otros módulos
export {
  OllamaAgent,
  OllamaAPIClient,
  ToolManager,
  MessageRole,
  interactiveChat
};
