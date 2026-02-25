"""
Workspace Skills Example - Custom Tools for GitHub Copilot SDK

This file demonstrates how to create custom tools using the @define_tool decorator
for use in your workspace's .copilot-skills/ directory.

USAGE:
======
1. Create a .copilot-skills/ directory at the root of your workspace:
   ```
   your-workspace/
   └── .copilot-skills/
       ├── custom_search.py    (copy and modify this example)
       ├── data_processor.py   (your custom tools)
       └── README.md           (optional: document your skills)
   ```

2. Copy this file (or your modified version) to .copilot-skills/

3. Define your tools using @define_tool decorator:
   ```python
   from pydantic import BaseModel, Field
   from copilot import define_tool

   class SearchParams(BaseModel):
       query: str = Field(..., description="Search query")
       limit: int = Field(default=10, description="Max results")

   @define_tool(description="Search your custom database")
   async def search_custom_db(query: str, limit: int = 10) -> dict:
       # Your implementation here
       return {"results": [...]}

   # Register as tool (tool name will be snake_case of function name)
   custom_search = define_tool(
       name="search_custom_db",
       description="Search your custom database for documents or data",
       params_type=SearchParams,
   )(search_custom_db)
   ```

4. The SDK will automatically discover and register your tools from .copilot-skills/

5. Use them in your conversation: "Use the search_custom_db tool to find..."

REQUIREMENTS:
=============
- Python 3.9+
- github-copilot-sdk (v0.1.25+)
- Any external dependencies your custom tools need
"""

from pydantic import BaseModel, Field
from copilot import define_tool


# ============================================================================
# Example 1: Simple Math Helper Tool
# ============================================================================

@define_tool(description="Perform common mathematical calculations")
async def calculate_math(operation: str, value1: float, value2: float = 0) -> dict:
    """
    Performs basic mathematical operations.
    
    Args:
        operation: One of 'add', 'subtract', 'multiply', 'divide', 'power', 'sqrt'
        value1: First number
        value2: Second number (for binary operations)
    
    Returns:
        Dictionary with 'result' and 'operation' keys
    """
    import math
    
    op_map = {
        "add": lambda a, b: a + b,
        "subtract": lambda a, b: a - b,
        "multiply": lambda a, b: a * b,
        "divide": lambda a, b: a / b if b != 0 else None,
        "power": lambda a, b: a ** b,
        "sqrt": lambda a, _: math.sqrt(a) if a >= 0 else None,
    }
    
    result = None
    if operation in op_map:
        try:
            result = op_map[operation](value1, value2)
        except Exception as e:
            return {"success": False, "error": str(e)}
    else:
        return {"success": False, "error": f"Unknown operation: {operation}"}
    
    return {
        "success": True,
        "operation": operation,
        "value1": value1,
        "value2": value2,
        "result": result,
    }


# ============================================================================
# Example 2: Text Processing Tool with Parameter Model
# ============================================================================

class TextProcessParams(BaseModel):
    """Parameters for text processing operations."""
    text: str = Field(..., description="The text to process")
    operation: str = Field(
        default="count_words",
        description="Operation: 'count_words', 'to_uppercase', 'to_lowercase', 'reverse', 'count_lines'"
    )


@define_tool(description="Process and analyze text content")
async def process_text(text: str, operation: str = "count_words") -> dict:
    """
    Processes text with various operations.
    
    Args:
        text: Input text to process
        operation: Type of processing to apply
    
    Returns:
        Dictionary with processing results
    """
    results = {
        "operation": operation,
        "input_length": len(text),
        "result": None,
    }
    
    if operation == "count_words":
        results["result"] = len(text.split())
    elif operation == "to_uppercase":
        results["result"] = text.upper()
    elif operation == "to_lowercase":
        results["result"] = text.lower()
    elif operation == "reverse":
        results["result"] = text[::-1]
    elif operation == "count_lines":
        results["result"] = len(text.split("\n"))
    else:
        results["error"] = f"Unknown operation: {operation}"
    
    return results


# ============================================================================
# Example 3: Advanced Tool with Complex Return Type
# ============================================================================

class DataAnalysisParams(BaseModel):
    """Parameters for data analysis."""
    data_points: list = Field(..., description="List of numbers to analyze")
    include_stats: bool = Field(default=True, description="Include statistical analysis")


@define_tool(description="Analyze numerical data and compute statistics")
async def analyze_data(data_points: list, include_stats: bool = True) -> dict:
    """
    Analyzes a list of numerical values.
    
    Args:
        data_points: List of numbers to analyze
        include_stats: Whether to include statistical analysis
    
    Returns:
        Dictionary with analysis results
    """
    if not data_points or not all(isinstance(x, (int, float)) for x in data_points):
        return {
            "error": "data_points must be a non-empty list of numbers",
            "success": False,
        }
    
    results = {
        "success": True,
        "count": len(data_points),
        "min": min(data_points),
        "max": max(data_points),
        "sum": sum(data_points),
    }
    
    if include_stats:
        import statistics
        try:
            results["mean"] = statistics.mean(data_points)
            results["median"] = statistics.median(data_points)
            if len(data_points) > 1:
                results["stdev"] = statistics.stdev(data_points)
        except Exception as e:
            results["stats_error"] = str(e)
    
    return results


# ============================================================================
# Tool Registration (Optional: explicit naming)
# ============================================================================
# The SDK will auto-discover tools from @define_tool decorated functions.
# You can optionally register them explicitly by assigning to variables:

math_tool = define_tool(
    name="calculate_math",
    description="Perform mathematical calculations (add, subtract, multiply, divide, power, sqrt)",
    params_type=BaseModel,  # Can be complex if needed
)(calculate_math)

text_processor = define_tool(
    name="process_text",
    description="Process and analyze text (count words, case conversion, etc.)",
    params_type=TextProcessParams,
)(process_text)

data_analyzer = define_tool(
    name="analyze_data",
    description="Analyze numerical data and compute statistics",
    params_type=DataAnalysisParams,
)(analyze_data)


# ============================================================================
# Example: Custom Implementation from Scratch
# ============================================================================
# If you need more control, implement the Tool class directly:
#
# from copilot.types import Tool
#
# async def my_custom_handler(query: str) -> str:
#     """Your tool logic here."""
#     return f"Processed: {query}"
#
# my_tool = Tool(
#     name="my_custom_tool",
#     description="My custom tool description",
#     handler=my_custom_handler,
#     parameters={}  # Add JSON Schema if complex params needed
# )


if __name__ == "__main__":
    """Test the example tools locally."""
    import asyncio

    async def main():
        # Test math tool
        result1 = await calculate_math("add", 10, 5)
        print("Math (10 + 5):", result1)

        # Test text processor
        result2 = await process_text("Hello World", "count_words")
        print("Text (count words):", result2)

        # Test data analyzer
        result3 = await analyze_data([1, 2, 3, 4, 5], include_stats=True)
        print("Data Analysis:", result3)

    asyncio.run(main())
