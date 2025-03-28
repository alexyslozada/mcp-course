# Ollama MCP Integration

Este proyecto permite la integración de [Ollama](https://ollama.ai/) con herramientas externas mediante el protocolo MCP (Machine Control Protocol), habilitando llamadas a funciones (function calling) desde modelos de lenguaje.

## Características

- Comunicación con API local de Ollama
- Integración con servidores MCP para extender las capacidades del LLM
- Soporte para "function calling" (llamada a funciones desde el LLM)
- Herramientas predefinidas y herramientas MCP personalizadas
- Interfaz de chat interactiva por consola

## Requisitos previos

- Python 3.9+
- [Ollama](https://ollama.ai/) instalado y en ejecución
- Al menos un modelo de lenguaje compatible con function calling (recomendado: `mistral:latest`)
- Node.js (para ejecutar el servidor MCP)

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/usuario/ollama-mcp-integration.git
cd ollama-mcp-integration
```

### 2. Crear y activar entorno virtual

```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En macOS/Linux
source venv/bin/activate
```

### 3. Instalar dependencias

Este proyecto utiliza `uv` como gestor de paquetes para Python. Las dependencias exactas están especificadas en el archivo `uv.lock`.

```bash
# Instalar uv si aún no lo tienes
pip install uv

# Instalar dependencias desde uv.lock
uv sync
```

Alternativamente, si necesitas instalar las dependencias manualmente:

```bash
uv pip install requests mcp-python-client python-dotenv
```

### 4. Configurar el servidor MCP

Asegúrate de tener el servidor MCP correctamente instalado y configurado:

```bash
# Instalar dependencias del servidor MCP
cd path/to/mcp-server
npm install

# Compilar el servidor MCP (si es necesario)
npm run build
```

## Configuración

Puedes personalizar la configuración mediante variables de entorno:

```bash
# Ruta al servidor MCP
export MCP_SERVER_PATH="/path/to/your/mcp-server/dist/server.js"

# URL de la API de Ollama (por defecto: http://localhost:11434)
export OLLAMA_API_URL="http://localhost:11434"
```

## Uso

### 1. Asegúrate de que Ollama esté en ejecución

```bash
ollama serve
```

### 2. Descarga un modelo compatible con function calling (si aún no lo tienes)

```bash
ollama pull mistral:latest
```

### 3. Ejecuta la aplicación

```bash
python ollama-python-app.py
```

### 4. Interactuar con el chat

Una vez iniciada la aplicación, podrás interactuar con el modelo a través de una interfaz de chat por consola:

- Escribe tu mensaje y presiona Enter
- Para invocar una herramienta, formula tu pregunta de manera que el modelo entienda que necesita usar una función
- Escribe `/salir`, `/exit` o `/quit` para terminar la sesión

## Estructura del proyecto

- `mcp_client.py` - Cliente para comunicarse con servidores MCP
- `ollama-python-app.py` - Aplicación principal que integra Ollama con MCP
- `requirements.txt` - Dependencias del proyecto

## Herramientas predefinidas

El sistema incluye dos herramientas de demostración:

1. `get_current_weather` - Obtiene el clima de una ciudad (simulado)
2. `sum_two_numbers` - Suma dos números

Además, se cargarán automáticamente todas las herramientas disponibles en el servidor MCP.

## Personalización

### Agregar nuevas herramientas integradas

Para agregar nuevas herramientas integradas, modifica la clase `ToolManager` en `ollama-python-app.py`:

```python
def __init__(self):
    self.built_in_tools = [
        # Herramientas existentes...
        
        # Nueva herramienta
        {
            'type': 'function',
            'function': {
                'name': 'mi_nueva_herramienta',
                'description': 'Descripción de lo que hace',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'param1': {
                            'type': 'string',
                            'description': 'Descripción del parámetro',
                        },
                    },
                    'required': ['param1'],
                },
            },
        },
    ]
```

Luego, implementa la lógica de la herramienta en la función `execute_function`.

### Cambiar el modelo predeterminado

Modifica la constante `DEFAULT_MODEL` en `ollama-python-app.py`:

```python
DEFAULT_MODEL = "llama3:latest"  # O cualquier otro modelo disponible
```

## Solución de problemas

### El servidor MCP no se puede conectar

Verifica que:
- La ruta al servidor MCP sea correcta
- El servidor Node.js esté funcionando
- Los permisos de ejecución sean adecuados

### Errores en las llamadas a funciones

- Verifica que el modelo tenga soporte para function calling (recomendados: mistral, llama3-70b)
- Revisa los logs para ver errores específicos en la ejecución de herramientas
- Asegúrate de que los argumentos pasados a las herramientas MCP tengan el formato correcto

### Ollama no está respondiendo

- Verifica que Ollama esté en ejecución (`ollama serve`)
- Comprueba que puedas acceder a la API en `http://localhost:11434`
- Asegúrate de tener al menos un modelo descargado (`ollama list`)

## Consejos para desarrolladores

1. Utiliza logging en lugar de print para un mejor seguimiento
2. Para extender funcionalidades, considera crear clases adicionales siguiendo el principio de responsabilidad única
3. Los modelos con mejor soporte para function calling son los de la familia Mistral y los modelos grandes de Llama (70B)

## Licencia

[MIT](LICENSE)
