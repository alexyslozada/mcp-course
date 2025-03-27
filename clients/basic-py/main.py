from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Crear los parámetros para la conexión stdio
server_params = StdioServerParameters(
    command="node",
    args=[
        "/Users/alexyslozada/github.com/alexyslozada/mcp-course/servers/basic/dist/server.js"
    ],
    env=None,
)

async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            """  lista los prompts disponibles """
            prompts = await session.list_prompts()
            print("Prompts:")
            print(prompts)

            """ ejecuta un prompt """
            prompt = await session.get_prompt(
                prompts.prompts[1].name,
                arguments={
                    "code": "console.log('Hello, world!');"
                }
            )
            print("Prompt:")
            print(prompt)

            """ listar los recursos disponibles """
            resources = await session.list_resources()
            print("Resources:")
            print(resources)
            
            """ listar los recursos dinámicos disponibles """
            template_resources = await session.list_resource_templates()
            print("Template Resources:")
            print(template_resources)

            """ obtener un recurso """
            resource = await session.read_resource("got://quotes/random")
            print("Resource:")
            print(resource)

            """ obtener un recurso dinámico """
            resource = await session.read_resource("person://properties/alexys")
            print("Resource:")
            print(resource)

            """ listar las herramientas disponibles """
            tools = await session.list_tools()
            print("Tools:")
            print(tools)

            """ ejecutar una herramienta """
            tool_result = await session.call_tool(
                tools.tools[1].name,
                arguments={
                    "numbers": [1, 2, 3, 4, 5]
                },
            )
            print("Tool Result:")
            print(tool_result)
    
if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
