# TP-API-MCP Sample Server

A comprehensive FastMCP (Model Context Protocol) server demonstrating various features and capabilities of the FastMCP framework. This sample server includes tools for mathematical operations, text processing, data analysis, utility functions, async operations, and context-aware functionality.

## 🚀 Features

### Basic Tools
- **Multi-language Greetings**: Greet users in different languages (English, Spanish, French, German, Italian, Portuguese)
- **Time Functions**: Get current date and time with custom formatting
- **Random Number Generation**: Generate random numbers within specified ranges

### Mathematical Operations
- **Safe Expression Evaluation**: Calculate mathematical expressions safely
- **List Operations**: Perform sum, average, min, max, count, and product operations on number lists

### Text Processing
- **Text Transformations**: Uppercase, lowercase, title case, reverse, word count, character count
- **List Analysis**: Analyze lists for duplicates, unique items, statistics

### Utility Functions
- **Todo List Creator**: Create formatted todo lists with priority levels
- **Password Generator**: Generate secure passwords with customizable criteria

### Advanced Features
- **Async Operations**: Countdown timer and random fact fetcher with async support
- **Context-Aware Tools**: Smart text summarization using LLM sampling
- **Error Handling**: Robust error handling with informative responses
- **Resources**: Structured data provision (server info, API examples)
- **Prompts**: Template prompts for code review and concept explanation

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- FastMCP library

### Install FastMCP
```bash
# Using uv (recommended)
uv add fastmcp

# Or using pip
pip install fastmcp
```

### Clone and Setup
```bash
git clone <your-repo-url>
cd TP_API_mcp
```

## 🏃‍♂️ Running the Server

### Method 1: Direct Python Execution
```bash
python main.py
```

### Method 2: Using FastMCP CLI
```bash
# Basic run
fastmcp run main.py

# With configuration file
fastmcp run

# Development mode with Inspector UI
fastmcp dev main.py
```

### Method 3: HTTP Transport
```bash
fastmcp run main.py --transport http --port 8000
```

## 🛠️ Available Tools

### Basic Tools

#### `greet(name: str, language: str = "english") -> str`
Greet a person in different languages.

**Example:**
```python
# English (default)
greet(name="Alice")
# Returns: "Hello, Alice!"

# Spanish
greet(name="Alice", language="spanish")
# Returns: "¡Hola, Alice!"
```

#### `get_current_time(format: str = "%Y-%m-%d %H:%M:%S") -> str`
Get current date and time with custom formatting.

**Example:**
```python
get_current_time()
# Returns: "2024-01-15 14:30:45"

get_current_time(format="%B %d, %Y at %I:%M %p")
# Returns: "January 15, 2024 at 02:30 PM"
```

### Mathematical Tools

#### `calculate(expression: str) -> Dict[str, Any]`
Safely evaluate mathematical expressions.

**Example:**
```python
calculate(expression="2 + 2 * 3")
# Returns: {"expression": "2 + 2 * 3", "result": 8, "type": "int"}
```

#### `math_operations(numbers: List[float], operation: str) -> Dict[str, Any]`
Perform mathematical operations on lists.

**Example:**
```python
math_operations(numbers=[1, 2, 3, 4, 5], operation="average")
# Returns: {"numbers": [1,2,3,4,5], "operation": "average", "result": 3.0}
```

### Text Processing Tools

#### `process_text(text: str, operation: str) -> Dict[str, Any]`
Process text with various operations.

**Available operations:** `uppercase`, `lowercase`, `title`, `reverse`, `word_count`, `char_count`, `remove_spaces`

**Example:**
```python
process_text(text="Hello World", operation="uppercase")
# Returns: {"original": "Hello World", "operation": "uppercase", "result": "HELLO WORLD"}
```

#### `analyze_list(items: List[str]) -> Dict[str, Any]`
Analyze a list of items and provide statistics.

**Example:**
```python
analyze_list(items=["apple", "banana", "apple", "cherry"])
# Returns: {
#   "total_items": 4,
#   "unique_items": 3,
#   "unique_list": ["apple", "banana", "cherry"],
#   "duplicates": ["apple"],
#   "longest_item": "banana",
#   "shortest_item": "apple",
#   "average_length": 5.5
# }
```

### Utility Tools

#### `create_todo_list(tasks: List[str], priority: str = "medium") -> Dict[str, Any]`
Create formatted todo lists with priorities.

**Priority levels:** `high` (🔴), `medium` (🟡), `low` (🟢)

#### `password_generator(length: int = 12, include_special: bool = True) -> Dict[str, Any]`
Generate secure passwords with strength assessment.

### Async Tools

#### `async_countdown(seconds: int) -> Dict[str, Any]`
Simulate an async countdown operation (1-10 seconds).

#### `fetch_random_fact() -> Dict[str, Any]`
Fetch a random interesting fact with simulated network delay.

### Context-Aware Tools

#### `smart_summary(text: str, max_sentences: int = 3, ctx: Context = None) -> str`
Create intelligent text summaries using LLM sampling when context is available.

## 📊 Resources

### `server-info`
Get comprehensive information about the server including features and metadata.

### `api-examples`
Get example API calls for all available tools with sample parameters.

## 📝 Prompts

### `code-review`
Generate comprehensive code review prompts with structured feedback guidelines.

### `explain-concept` 
Generate prompts for explaining concepts to different audiences.

## 🧪 Testing the Server

### Using FastMCP Client
```python
import asyncio
from fastmcp import Client

async def test_server():
    client = Client("main.py")  # or Client("http://localhost:8000")
    
    async with client:
        # Test basic greeting
        result = await client.call_tool("greet", {"name": "World", "language": "french"})
        print(result.data)  # "Bonjour, World!"
        
        # Test calculation
        result = await client.call_tool("calculate", {"expression": "10 + 5 * 2"})
        print(result.data)  # {"expression": "10 + 5 * 2", "result": 20, "type": "int"}

asyncio.run(test_server())
```

### Using curl (HTTP transport)
```bash
# Start server with HTTP transport
fastmcp run main.py --transport http --port 8000

# Test endpoint
curl -X POST http://localhost:8000/tools/greet \
  -H "Content-Type: application/json" \
  -d '{"name": "World", "language": "spanish"}'
```

## 🔧 Configuration

The server includes a `fastmcp.json` configuration file with:
- Source path and entrypoint configuration
- Environment setup with Python version requirements
- Deployment settings for transport and logging
- Metadata including description, version, and tags

## 🐛 Error Handling

The server includes comprehensive error handling:
- Input validation with helpful error messages
- Safe mathematical expression evaluation
- Graceful fallbacks for context-dependent operations
- Detailed error responses with context information

## 📚 Development

### Development Mode
```bash
# Start with Inspector UI for debugging
fastmcp dev main.py

# This will start the server and open a web interface for inspection
```

### Adding New Tools
1. Define your function with proper type hints
2. Add the `@mcp.tool` decorator
3. Include a comprehensive docstring
4. Handle errors gracefully
5. Return structured data when appropriate

**Example:**
```python
@mcp.tool
def your_new_tool(param: str) -> Dict[str, Any]:
    """Description of what your tool does."""
    try:
        # Your logic here
        result = process_param(param)
        return {"input": param, "output": result}
    except Exception as e:
        return {"error": str(e), "input": param}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Inspired by the Model Context Protocol (MCP) specification
- Thanks to the FastMCP community for excellent documentation and examples
