/**
 * Show Alert Box Tool
 * Displays a browser alert dialog with a custom message
 */
class ShowAlertTool extends FunctionCallDefinition {
  constructor() {
    super(
      "show_alert",
      "Displays an alert dialog box with a message to the user",
      {
        type: "object",
        properties: {
          message: {
            type: "string",
            description: "The message to display in the alert box"
          },
          title: {
            type: "string",
            description: "Optional title prefix for the alert message"
          }
        }
      },
      ["message"]
    );
  }

  functionToCall(parameters) {
    const message = parameters.message || "Alert!";
    const title = parameters.title;

    // Construct the full alert message
    const fullMessage = title ? `${title}: ${message}` : message;

    // Show the alert
    alert(fullMessage);

    console.log(` Alert shown: ${fullMessage}`);
  }
}
/**
 * Add CSS Style Tool
 * Injects CSS styles into the current page with !important flag
 */
class AddCSSStyleTool extends FunctionCallDefinition {
  constructor() {
    super(
      "add_css_style",
      "Injects CSS styles into the current page with !important flag",
      {
        type: "object",
        properties: {
          selector: {
            type: "string",
            description: "CSS selector to target elements (e.g., 'body', '.class', '#id')"
          },
          property: {
            type: "string",
            description: "CSS property to set (e.g., 'background-color', 'font-size', 'display')"
          },
          value: {
            type: "string",
            description: "Value for the CSS property (e.g., 'red', '20px', 'none')"
          },
          styleId: {
            type: "string",
            description: "Optional ID for the style element (for updating existing styles)"
          }
        }
      },
      ["selector", "property", "value"]
    );
  }

  functionToCall(parameters) {
    const { selector, property, value, styleId } = parameters;

    // Create or find the style element
    let styleElement;
    if (styleId) {
      styleElement = document.getElementById(styleId);
      if (!styleElement) {
        styleElement = document.createElement('style');
        styleElement.id = styleId;
        document.head.appendChild(styleElement);
      }
    } else {
      styleElement = document.createElement('style');
      document.head.appendChild(styleElement);
    }

    // Create the CSS rule with !important
    const cssRule = `${selector} { ${property}: ${value} !important; }`;

    // Add the CSS rule to the style element
    if (styleId) {
      // If using an ID, replace the content
      styleElement.textContent = cssRule;
    } else {
      // Otherwise append to any existing content
      styleElement.textContent += cssRule;
    }

    console.log(`🎨 CSS style injected: ${cssRule}`);
    console.log(`   Applied to ${document.querySelectorAll(selector).length} element(s)`);
  }
}

/**
 * Search Memory Tool
 * Queries the AURA Persistent Memory (Pinecone) for contextual past interactions
 */
class SearchMemoryTool extends FunctionCallDefinition {
  constructor() {
    super(
      "search_persistent_memory",
      "Searches your long-term persistent memory for past interactions, coding context, screen observations, or tasks you've previously done with the user.",
      {
        type: "object",
        properties: {
          query: {
            type: "string",
            description: "The semantic search query to look up in the memory database (e.g., 'What was I coding yesterday?', 'Flutter animations')"
          },
          filter_type: {
            type: "string",
            description: "Optional filter for memory type (e.g., 'conversation', 'screen', 'task'). Leave blank to search all types."
          }
        }
      },
      ["query"]
    );
  }

  async functionToCall(parameters) {
    const { query, filter_type } = parameters;
    console.log(`🧠 Searching memory for: "${query}" (Type: ${filter_type || 'all'})`);

    try {
      const backendUrl = (document.getElementById("backendUrl") ? document.getElementById("backendUrl").value.replace(/\/$/, "") : "") || "https://aura-jet-eight.vercel.app";
      const response = await fetch(`${backendUrl}/api/memory/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          filter_type: filter_type,
          top_k: 5
        })
      });

      const data = await response.json();
      
      if (data.error) {
        return `Memory Search Error: ${data.error}`;
      }

      if (!data.memories || data.memories.length === 0) {
        return "No relevant past memories found.";
      }

      // Format the memories into a readable string for the model
      const formattedMemories = data.memories.map(m => 
        `[Date: ${new Date(m.timestamp).toLocaleString()}] [Type: ${m.memory_type}] [Relevance: ${(m.score * 100).toFixed(1)}%]:\n${m.content}\n`
      ).join("\n---\n");

      return `--- RETRIEVED MEMORIES ---\n${formattedMemories}`;

    } catch (error) {
      console.error("Memory search failed:", error);
      return `Failed to connect to memory core: ${error.message}`;
    }
  }
}

