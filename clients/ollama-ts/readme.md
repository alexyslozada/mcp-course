# Ollama TypeScript Client with MCP Integration

Este proyecto es un cliente de TypeScript para interactuar con Ollama y servidores MCP (Machine Control Protocol). Permite establecer conversaciones con modelos de lenguaje de Ollama y ejecutar herramientas tanto integradas como proporcionadas por un servidor MCP.

## Requisitos previos

Antes de comenzar, asegúrate de tener instalado:

- [Node.js](https://nodejs.org/) (v16 o superior)
- [npm](https://www.npmjs.com/) (normalmente viene con Node.js)
- [Ollama](https://ollama.ai/) instalado y ejecutándose en tu sistema
- Un servidor MCP (para las funcionalidades de herramientas externas)

## Configuración del proyecto

### 1. Clonar o crear el proyecto

```bash
# Crea el directorio del proyecto
mkdir ollama-ts-app
cd ollama-ts-app

# Copia los archivos del proyecto
# - mcpClient.ts
# - ollamaApp.ts
# - package.json
# - tsconfig.json
```

### 2. Instalar dependencias

```bash
npm install
```

### 3. Configuración del entorno

Por defecto, el proyecto está configurado para conectarse a:
- Ollama en `http://localhost:11434`
- Un servidor MCP ejecutado con Node.js en la ruta especificada en la variable de entorno `MCP_SERVER_PATH`

Puedes modificar estas configuraciones editando las constantes al inicio de `ollamaApp.ts` o estableciendo la variable de entorno `MCP_SERVER_PATH`.

```bash
# Ejemplo de configuración de la variable de entorno
export MCP_SERVER_PATH=/ruta/a/tu/servidor/mcp/server.js
```

## Compilación

Para compilar el proyecto TypeScript a JavaScript:

```bash
npm run build
```

Esto generará los archivos JavaScript en el directorio `dist/`.

## Ejecución

### Iniciar la aplicación

```bash
npm start
```

O si prefieres ejecutar directamente con ts-node durante el desarrollo:

```bash
npm run dev
```

### Uso del chat interactivo

Una vez iniciada la aplicación:

1. La aplicación verificará la conexión con Ollama y el servidor MCP
2. Se iniciará un chat interactivo donde puedes:
   - Escribir mensajes que serán procesados por el modelo seleccionado
   - Ver las respuestas del modelo
   - Observar cuando el modelo decide ejecutar herramientas
   - Escribir `/salir`, `/exit` o `/quit` para terminar la sesión

## Estructura del proyecto

- `mcpClient.ts`: Cliente para interactuar con servidores MCP
- `ollamaApp.ts`: Implementación principal con clientes de Ollama, gestor de herramientas y chat interactivo
- `package.json`: Configuración del proyecto, dependencias y scripts
- `tsconfig.json`: Configuración de TypeScript

## Personalización

### Agregar nuevas herramientas integradas

Para agregar nuevas herramientas integradas, edita la clase `ToolManager` en `ollamaApp.ts` y añade tu herramienta al array `builtInTools`. Luego implementa la lógica de ejecución en la función `executeFunction`.

### Cambiar el modelo predeterminado

Modifica la constante `DEFAULT_MODEL` en `ollamaApp.ts` para utilizar un modelo diferente.

## Solución de problemas

### El servidor Ollama no está disponible

Asegúrate de que Ollama esté instalado y ejecutándose. Puedes verificar su estado con:

```bash
ollama list
```

### Error de conexión con el servidor MCP

Verifica que:
1. La ruta al servidor MCP sea correcta
2. El servidor MCP esté ejecutándose
3. El servidor implemente correctamente el protocolo MCP

## Dependencias principales

- `@modelcontextprotocol/sdk`: SDK para interactuar con servidores MCP
- `node-fetch`: Para realizar solicitudes HTTP a la API de Ollama
- `typescript`: Para la compilación de TypeScript a JavaScript
