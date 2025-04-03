import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { createTodo, getAllTodos, clearCompletedTodos, completeTodo, deleteTodo, updateTodoTask } from "./todo/todo.service.js";

// Create server instance
const server = new McpServer({
    name: "TODO List MCP Server",
    version: "1.0.0",
    capabilities: {
      tools: {},
    },
  });

server.tool(
    "TODO-Create",
    "Create a new todo item",
    {
        task: z.string().describe("The task to add to the todo list"),
    },
    async ({task}) => {
        const todo = createTodo(task);
        return {
            content: [{
                type: "text",
                text: `Todo created: ${todo.task}`,
            }],
        };
    }
)

server.tool(
    "TODO-List",
    "List all todo items",
    {},
    async () => {
        const todos = getAllTodos();
        return {
            content: [{type: "text", text: JSON.stringify(todos, null, 2)}],
        };
    }
)

server.tool(
    "TODO-ClearCompleted",
    "Clear all completed todo items",
    {},
    async () => {
        clearCompletedTodos();
        return {
            content: [{type: "text", text: "All completed todos cleared"}],
        };
    }
)

server.tool(
    "TODO-Complete",
    "Complete a todo item",
    {
        id: z.string().describe("The id of the todo item to complete"),
    },  
    async ({id}) => {
        const todo = completeTodo(id);
        return {
            content: [{type: "text", text: `Todo completed: ${todo?.task}`}],
        };
    }
)   

server.tool(
    "TODO-Delete",
    "Delete a todo item",
    {
        id: z.string().describe("The id of the todo item to delete"),
    },
    async ({id}) => {
        const success = deleteTodo(id);
        return {
            content: [{type: "text", text: `Todo deleted: ${success ? "Success" : "Failed"}`}],
        };
    }
)   

server.tool(
    "TODO-Update",
    "Update a todo item",
    {
        id: z.string().describe("The id of the todo item to update"),
        task: z.string().describe("The new task for the todo item"),
    },
    async ({id, task}) => {
        const todo = updateTodoTask(id, task);
        return {
            content: [{type: "text", text: `Todo updated: ${todo?.task}`}],
        };
    }
)

async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error("[INFO] Weather MCP Server running on stdio");
  }
  
  main().catch((error) => {
    console.error("[ERROR] Fatal error in main():", error);
    process.exit(1);
  });