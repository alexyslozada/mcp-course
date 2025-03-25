# Servicio MCP Básico

Este es un servicio MCP (Model Context Protocol) que proporciona varias funcionalidades, incluyendo citas de Game of Thrones y operaciones matemáticas.

## Requisitos Previos

- Node.js (versión 16 o superior)
- npm (administrador de paquetes de Node.js)

## Pasos para Ejecutar el Servicio

1. **Instalar Dependencias**
   ```bash
   npm install
   ```

2. **Compilar el Proyecto**
   ```bash
   npm run build
   ```

3. **Ejecutar el Servicio**
   ```bash
   npm start
   ```

## Funcionalidades Incluidas

El servicio incluye las siguientes herramientas:

- **get_random_quotes**: Obtiene citas aleatorias de Game of Thrones
- **lcm**: Calcula el mínimo común múltiplo de una lista de números
- **person-properties**: Accede a información de personas registradas
- **got_quotes_analysis**: Analiza citas de Game of Thrones
- **code_review**: Proporciona una estructura para revisión de código

## Estructura del Proyecto

- `src/server.ts`: Archivo principal del servidor
- `dist/`: Directorio donde se genera el código compilado
- `package.json`: Configuración del proyecto y dependencias
- `tsconfig.json`: Configuración de TypeScript

## Solución de Problemas

Si encuentras algún error durante la instalación o ejecución:

1. Asegúrate de tener la versión correcta de Node.js instalada
2. Intenta eliminar la carpeta `node_modules` y el archivo `package-lock.json`, luego ejecuta `npm install` nuevamente
3. Verifica que todos los archivos estén en la ubicación correcta según la estructura del proyecto

## Notas Adicionales

- El servicio se ejecuta como un proceso en segundo plano
- Los logs y errores se mostrarán en la consola
- Para detener el servicio, presiona Ctrl+C en la terminal 