import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

/**
 * Cliente para interactuar con servidores MCP (Machine Control Protocol).
 * 
 * Este cliente permite establecer una conexión con un servidor MCP,
 * listar las herramientas disponibles y ejecutarlas.
 * 
 * Ejemplo de uso:
 * ```typescript
 * const client = new MCPClient("node", ["path/to/server.js"]);
 * await client.connect();
 * const tools = await client.listTools();
 * console.log(tools);
 * 
 * const result = await client.executeTool("tool_name", { arg1: "value1" });
 * console.log(result);
 * ```
 */
export class MCPClient {
  private serverParams: {
    command: string;
    args: string[];
    env?: Record<string, string>;
  };
  private client: Client | null = null;
  private transport: StdioClientTransport | null = null;

  /**
   * Inicializa un cliente MCP.
   * 
   * @param command El comando para ejecutar el servidor MCP (e.j. "node", "python")
   * @param args Los argumentos para el comando (e.j. ["path/to/server.js"])
   * @param env Variables de entorno para el servidor
   */
  constructor(
    command: string,
    args: string[],
    env?: Record<string, string>
  ) {
    this.serverParams = {
      command,
      args,
      env
    };
  }

  /**
   * Establece conexión con el servidor MCP.
   * 
   * @returns True si la conexión fue exitosa, False en caso contrario
   */
  async connect(): Promise<boolean> {
    try {
      // Crear el transporte
      this.transport = new StdioClientTransport(this.serverParams);

      // Configurar el cliente
      this.client = new Client(
        {
          name: "mcp-typescript-client",
          version: "1.0.0"
        },
        {
          capabilities: {
            prompts: {},
            resources: {},
            tools: {}
          }
        }
      );

      // Conectar al servidor
      await this.client.connect(this.transport);

      console.log("Conexión exitosa con servidor MCP");
      return true;
    } catch (e) {
      if (e instanceof Error) {
        if (e.message.includes("connect")) {
          console.error(`Error de conexión con servidor MCP: ${e}`);
        } else {
          console.error(`Error desconocido al conectar con servidor MCP: ${e}`);
        }
      }
      await this.disconnect();
      return false;
    }
  }

  /**
   * Cierra la conexión con el servidor MCP
   */
  async disconnect(): Promise<void> {
    try {
      if (this.client) {
        await this.client.close();
        this.client = null;
      }

      this.transport = null;

      console.log("Desconexión exitosa del servidor MCP");
    } catch (e) {
      console.error(`Error durante la desconexión: ${e}`);
    }
  }

  /**
   * Lista todas las herramientas disponibles en el servidor
   * 
   * @returns Objeto con información sobre las herramientas disponibles
   * @throws Error Si el cliente no está conectado o hay un error al listar las herramientas
   */
  async listTools(): Promise<any> {
    if (!this.client) {
      throw new Error("Cliente no conectado. Llama a connect() primero");
    }

    try {
      const tools = await this.client.listTools();
      console.debug(`Herramientas disponibles: ${JSON.stringify(tools)}`);
      return tools;
    } catch (e) {
      console.error(`Error al listar herramientas: ${e}`);
      throw e;
    }
  }

  /**
   * Ejecuta una herramienta específica con los argumentos proporcionados
   * 
   * @param toolName Nombre de la herramienta a ejecutar
   * @param arguments Argumentos para la herramienta
   * @returns Resultado de la ejecución de la herramienta
   * @throws Error Si el cliente no está conectado o hay un error al ejecutar la herramienta
   */
  async executeTool(toolName: string, args: Record<string, any>): Promise<any> {
    if (!this.client) {
      throw new Error("Cliente no conectado. Llama a connect() primero");
    }

    try {
      console.debug(`Ejecutando herramienta ${toolName} con argumentos: ${JSON.stringify(args)}`);
      const result = await this.client.callTool({
        name: toolName,
        arguments: args
      });

      console.debug(`Resultado de la herramienta ${toolName}: ${JSON.stringify(result)}`);
      return result;
    } catch (e) {
      console.error(`Error al ejecutar herramienta ${toolName}: ${e}`);
      throw e;
    }
  }

  /**
   * Obtiene la instancia del cliente MCP
   * @returns La instancia del cliente o null si no está conectado
   */
  getClient(): Client | null {
    return this.client;
  }
}
