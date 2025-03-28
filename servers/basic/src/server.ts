import { McpServer, ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import fetch from "node-fetch";

const GOT_API_BASE = "https://api.gameofthronesquotes.xyz/v1";

// Type definitions for the Game of Thrones API response
interface Quote {
  sentence: string;
  character: Character;
}

interface Character {
  name: string;
  slug: string;
  house: House;
}

interface House {
  name: string;
  slug: string;
}

// Function to fetch random quotes from the Game of Thrones API
async function fetchRandomQuotes(count: number): Promise<Quote[]> {
  if (count <= 0) {
    throw new Error("count must be a positive number");
  }
  if (count > 10) {
    throw new Error("maximum number of quotes is 10");
  }

  const url = `${GOT_API_BASE}/random/${count}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Error fetching quotes: ${response.statusText}`);
  }

  return await response.json() as Quote[];
}

// Function to format a quote into a readable string
function formatQuote(quote: Quote): string {
  return `
Quote: "${quote.sentence}"
Character: ${quote.character.name}
House: ${quote.character.house.name}`;
}

// Create an MCP server
const server = new McpServer({
  name: "Game of Thrones Quotes",
  version: "1.0.0",
  capabilities: {
    resources: { listChanged: true },
    tools: {},
    prompts: {}
  }
});

// Add get_random_quotes tool
server.tool(
  "get_random_quotes",
  { count: z.number().optional().default(5) },
  async ({ count }) => {
    try {
      // Validate count
      if (count <= 0) {
        return {
          content: [{ type: "text", text: "Count must be a positive number." }],
          isError: true
        };
      }
      if (count > 10) {
        return {
          content: [{ type: "text", text: "Maximum number of quotes is 10." }],
          isError: true
        };
      }

      // Fetch quotes from API
      const quotes = await fetchRandomQuotes(count);

      // Format quotes
      const formattedQuotes = quotes.map(formatQuote);

      return {
        content: [{ type: "text", text: formattedQuotes.join("\n---\n") }]
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: `Error: ${(error as Error).message}` }],
        isError: true
      };
    }
  }
);

// Add lcm (least common multiple) tool
server.tool(
  "lcm",
  "Calculate the least common multiple of a list of numbers",
  { numbers: z.array(z.number()).min(2).describe("A list of numbers to calculate the least common multiple of. The list must contain at least two numbers.") },
  async ({ numbers }) => {
    try {
      // Calculate LCM
      let result = Math.floor(numbers[0]);
      for (let i = 1; i < numbers.length; i++) {
        const num = Math.floor(numbers[i]);
        result = lcm(result, num);
      }

      return {
        content: [{ type: "text", text: `The least common multiple is: ${result}` }]
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: `Error: ${(error as Error).message}` }],
        isError: true
      };
    }
  }
);

// GCD and LCM helper functions
function gcd(a: number, b: number): number {
  while (b !== 0) {
    const temp = b;
    b = a % b;
    a = temp;
  }
  return a;
}

function lcm(a: number, b: number): number {
  return Math.abs(a * b) / gcd(a, b);
}

// Add random quotes resource
server.resource(
  "random-quotes",
  "got://quotes/random",
  async (uri) => {
    try {
      // Fetch 5 random quotes
      const quotes = await fetchRandomQuotes(5);

      // Format quotes
      const formattedQuotes = quotes.map(formatQuote);

      return {
        contents: [{
          uri: uri.href,
          text: formattedQuotes.join("\n---\n"),
          mimeType: "text/plain"
        }]
      };
    } catch (error) {
      throw new Error(`Error fetching quotes: ${(error as Error).message}`);
    }
  }
);

// Add person properties resource template
type PersonData = {
  name: string;
  age: number;
  height: number;
}

const personData: Record<string, PersonData> = {
  alexys: {
    name: "alexys",
    age: 23,
    height: 1.7
  },
  mariana: {
    name: "mariana",
    age: 23,
    height: 1.7
  }
};

server.resource(
  "person-properties",
  new ResourceTemplate("person://properties/{name}", { list: undefined }),
  async (uri, { name }) => {
    try {
      if (!name || Array.isArray(name)) {
        throw new Error("name must be a single string");
      }

      const person = personData[name];
      if (!person) {
        throw new Error(`Person with name ${name} not found`);
      }

      return {
        contents: [{
          uri: uri.href,
          text: JSON.stringify(person),
          mimeType: "application/json"
        }]
      };
    } catch (error) {
      throw new Error(`Error fetching person data: ${(error as Error).message}`);
    }
  }
);

// Add Game of Thrones quotes analysis prompt
server.prompt(
  "got_quotes_analysis",
  { theme: z.string().optional() },
  async ({ theme }) => {
    try {
      // Fetch 5 random quotes
      const quotes = await fetchRandomQuotes(5);

      // Format quotes
      const formattedQuotes = quotes.map(formatQuote);
      const quotesText = formattedQuotes.join("\n---\n");

      // Create theme instruction if provided
      const themeInstruction = theme
        ? ` Focus your analysis on the theme of '${theme}'.`
        : "";

      const systemContent =
        `You are an expert on Game of Thrones. Analyze these quotes and provide insights about the characters and their motivations.${themeInstruction}`;

      return {
        description: "Game of Thrones Quotes Analysis",
        messages: [
          {
            role: "assistant",
            content: {
              type: "text",
              text: systemContent
            }
          },
          {
            role: "user",
            content: {
              type: "text",
              text: `Here are some Game of Thrones quotes to analyze:\n\n${quotesText}`
            }
          }
        ]
      };
    } catch (error) {
      throw new Error(`Error generating quotes analysis prompt: ${(error as Error).message}`);
    }
  }
);

// Add code review prompt
server.prompt(
  "code_review",
  { code: z.string() },
  async ({ code }) => {
    if (!code) {
      throw new Error("No code provided for review");
    }

    return {
      description: "Code Review",
      messages: [
        {
          role: "assistant",
          content: {
            type: "text",
            text: "You are an expert software engineer with extensive experience in code review. You will help review code with a focus on:" +
              "\n- Code quality and best practices" +
              "\n- Performance considerations" +
              "\n- Security implications" +
              "\n- Maintainability and readability" +
              "\n- Potential bugs or edge cases" +
              "\nPlease share the code you would like me to review."
          }
        },
        {
          role: "user",
          content: {
            type: "text",
            text: `Please review the following code and provide detailed feedback:\n\n${code}`
          }
        }
      ]
    };
  }
);

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch(error => {
  console.error(`Server error: ${error.message}`);
  process.exit(1);
});
