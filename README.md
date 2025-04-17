# Chain of Thought Calculator

A sophisticated mathematical reasoning system that combines LLM-powered step-by-step problem solving with robust calculation tools and validation mechanisms.

## Table of Contents
- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Features](#features)
- [Components](#components)
- [Tool Functions](#tool-functions)
- [Advanced Features](#advanced-features)
- [Error Handling](#error-handling)
- [Usage Examples](#usage-examples)
- [Setup and Requirements](#setup-and-requirements)

## Overview

This system implements a Chain of Thought (CoT) calculator that combines the power of Large Language Models (specifically Google's Gemini) with precise mathematical tools. It breaks down complex mathematical problems into step-by-step solutions while maintaining accuracy through multiple validation layers.

## System Architecture

The system consists of two main components:

1. **Main Controller (`cot_main.py`)**
   - Manages the conversation flow
   - Handles LLM interactions
   - Coordinates tool execution
   - Implements validation and error handling
   - Maintains conversation history

2. **Tool Implementation (`cot_tools.py`)**
   - Provides core calculation functionality
   - Implements verification mechanisms
   - Handles reasoning visualization
   - Manages consistency checks
   - Provides fallback mechanisms

## Features

### Core Functionality
- Step-by-step mathematical problem solving
- Real-time calculation verification
- Detailed reasoning visualization
- Consistency checking across steps
- JSON-based function calling

### Advanced Features

#### 1. Self-Check Mechanism
- Automatic validation after calculations
- Reasonableness assessment
- Order of magnitude verification
- Mathematical rule compliance checking

#### 2. JSON Validation
- Strict JSON format validation
- Required field verification
- Type checking for parameters
- Graceful error handling

#### 3. Fallback System
- Error recovery mechanisms
- Uncertainty handling
- Alternative approach suggestions
- Detailed error reporting

## Components

### 1. Main Controller (`cot_main.py`)

#### Key Functions:
- `validate_json(function_call: str)`: Validates function call JSON format
- `handle_tool_error(session, error_msg, step_context)`: Manages tool execution errors
- `get_llm_response(client, prompt)`: Handles LLM interactions
- `generate_with_timeout(client, prompt, timeout)`: Manages LLM response timeouts

### 2. Tool Implementation (`cot_tools.py`)

#### Core Tools:
```python
@mcp.tool()
def show_reasoning(steps: list)
def calculate(expression: str)
def verify(expression: str, expected: float)
def check_consistency(steps: list)
def fallback_reasoning(step_description: str)
```

## Tool Functions

### 1. Show Reasoning
- Displays step-by-step problem-solving process
- Formats steps in visual panels
- Maintains reasoning history

### 2. Calculate
- Performs mathematical calculations
- Handles various mathematical operations
- Includes error checking
- Triggers self-check mechanism

### 3. Verify
- Validates calculation results
- Compares expected vs actual results
- Provides detailed verification feedback

### 4. Check Consistency
- Analyzes step coherence
- Verifies mathematical progression
- Checks magnitude relationships
- Identifies potential issues

### 5. Fallback Reasoning
- Handles calculation errors
- Manages uncertainty cases
- Provides alternative approaches
- Documents error contexts

## Advanced Features

### 1. JSON Validation System
```python
def validate_json(function_call: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    # Validates:
    # - JSON structure
    # - Required fields (name, args)
    # - Field types
    # Returns validation status, parsed JSON, and message
```

### 2. Self-Check Implementation
```python
self_check_prompt = """
Given the calculation:
Expression: {expression}
Result: {value}

Please perform an internal self-check:
1. Does this result seem reasonable?
2. Are the orders of magnitude correct?
3. Have I followed proper mathematical rules?
4. Is there any obvious error?
"""
```

### 3. Error Handling System
```python
async def handle_tool_error(session, error_msg: str, step_context: str) -> str:
    # Manages tool execution errors
    # Triggers fallback mechanism
    # Maintains conversation flow
    # Returns appropriate prompt updates
```

## Usage Examples

### 1. Basic Calculation
```python
Assistant: FUNCTION_CALL: {"name": "calculate", "args": {"expression": "2 + 3"}}
```

### 2. Verification
```python
Assistant: FUNCTION_CALL: {"name": "verify", "args": {"expression": "2 + 3", "expected": 5}}
```

### 3. Fallback Usage
```python
Assistant: FUNCTION_CALL: {"name": "fallback_reasoning", "args": {"step_description": "Uncertain about division by zero"}}
```

## Setup and Requirements

### Dependencies
- Python 3.7+
- Google Gemini API
- Rich (for console formatting)
- MCP (Message Control Protocol)
- dotenv (for environment variables)

### Environment Variables
```
GEMINI_API_KEY=your_api_key_here
```

### Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables
4. Run the main script: `python cot_main.py`

## Error Handling

The system implements multiple layers of error handling:

1. **Tool Execution Errors**
   - Automatic fallback triggering
   - Error context preservation
   - Recovery suggestions

2. **Validation Errors**
   - JSON structure validation
   - Parameter type checking
   - Required field verification

3. **Calculation Errors**
   - Mathematical error handling
   - Division by zero protection
   - Overflow checking

4. **LLM Response Errors**
   - Timeout handling
   - Response validation
   - Fallback mechanisms

## Best Practices

1. **Error Recovery**
   - Always use fallback mechanisms for errors
   - Maintain conversation context
   - Provide clear error messages

2. **Validation**
   - Validate all JSON function calls
   - Check calculation results
   - Verify step consistency

3. **Documentation**
   - Document all error cases
   - Maintain clear step descriptions
   - Log important operations

## Contributing

Feel free to contribute to this project by:
1. Reporting issues
2. Suggesting enhancements
3. Submitting pull requests
4. Improving documentation

## License

This project is licensed under the GPL (General Public License).