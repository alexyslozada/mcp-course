from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Calculator MCP Server")

def add(a: float, b: float) -> float:
    return float(a + b)

def subtract(a: float, b: float) -> float:
    return float(a - b)

def multiply(a: float, b: float) -> float:
    return float(a * b)

def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("No se puede dividir por cero")
    return float(a / b)

@mcp.tool()
def calculate(a: float, b: float, operation: str) -> float:
    if operation == "add":
        return add(a, b)
    elif operation == "subtract":
        return subtract(a, b)
    elif operation == "multiply":
        return multiply(a, b)
    elif operation == "divide":
        return divide(a, b)
    else:
        raise ValueError("Operación no válida")

if __name__ == "__main__":
    mcp.run(transport='stdio')
