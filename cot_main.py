import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai
import asyncio
from rich.console import Console
from rich.panel import Panel
import json
from typing import Tuple, Optional, Dict, Any

console = Console()

# Load environment variables and setup Gemini
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content with a timeout"""
    try:
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
            ),
            timeout=timeout
        )
        return response
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return None

async def get_llm_response(client, prompt):
    """Get response from LLM with timeout"""
    response = await generate_with_timeout(client, prompt)
    if response and response.text:
        return response.text.strip()
    return None

def validate_json(function_call: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Validates the JSON structure in a function call string.
    
    Args:
        function_call: String starting with 'FUNCTION_CALL: ' followed by JSON
        
    Returns:
        Tuple containing:
        - bool: Whether validation passed
        - Optional[Dict]: Parsed JSON if valid, None if invalid
        - str: Validation message
    """
    try:
        # Extract JSON part after FUNCTION_CALL:
        if not function_call.startswith("FUNCTION_CALL: "):
            return False, None, "Invalid format: Must start with 'FUNCTION_CALL: '"
            
        json_str = function_call.replace("FUNCTION_CALL: ", "", 1)
        
        # Parse JSON
        parsed_json = json.loads(json_str)
        
        # Validate required fields
        if not isinstance(parsed_json, dict):
            return False, None, "Invalid JSON: Must be an object"
            
        if "name" not in parsed_json:
            return False, None, "Missing required field: 'name'"
            
        if not isinstance(parsed_json["name"], str):
            return False, None, "Invalid field: 'name' must be a string"
            
        if "args" not in parsed_json:
            return False, None, "Missing required field: 'args'"
            
        if not isinstance(parsed_json["args"], dict):
            return False, None, "Invalid field: 'args' must be an object"
            
        return True, parsed_json, "Validation successful"
        
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON format: {str(e)}"
    except Exception as e:
        return False, None, f"Validation error: {str(e)}"

async def handle_tool_error(session, error_msg: str, step_context: str) -> str:
    """
    Handle tool errors by calling fallback_reasoning
    Returns the fallback message for the conversation
    """
    fallback_description = f"Error in step: {step_context}\nError details: {error_msg}"
    await session.call_tool("fallback_reasoning", arguments={"step_description": fallback_description})
    return f"\nUser: Error occurred. Fallback triggered. Please reconsider this step or try an alternative approach."

async def main():
    try:
        console.print(Panel("Chain of Thought Calculator", border_style="cyan"))

        server_params = StdioServerParameters(
            command="python",
            args=["cot_tools.py"]
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                system_prompt = """You are a mathematical reasoning agent that solves problems step by step, tags the reasoning type, performs internal self-checks, and uses tools when appropriate.
                You have access to these tools:
                show_reasoning(steps: list) - Display your reasoning steps. Each step must include a label for the type of reasoning (e.g., arithmetic, logic, pattern).
                calculate(expression: str)- Calculate the result of an expression.
                verify(expression: str, expected: float) - Check if a calculation is correct.
                fallback(reason: str) - Use this if a tool fails or you are uncertain how to proceed.

                
                Instructions:
                1. Always start with reasoning. Use show_reasoning to break down the problem with labeled steps. This is mandatory for all the prompt you might get.
                2. Tag each step with the type of reasoning used: Eg: ""Arithmetic", "Logical" and "Entity Lookup". This is mandatory for all step.
                3. Then calculate using calculate().
                4. After each calculation, verify using verify().
                5. If you are unsure, or a tool result is inconsistent, call fallback() with an explanation.
                6. Before giving the final answer, re-check the logic and calculations, and state explicitly if they pass self-checks.
                7. Respond with exactly ONE line in one of the following formats:
                        FUNCTION_CALL: {"name": "function_name", "args": {"arg1": "value1", "arg2": "value2", ...}}
                        FINAL_ANSWER: [answer]


                Example:
                User: Solve (2 + 3) * 4
                Assistant: FUNCTION_CALL: show_reasoning|["1. First, solve inside parentheses: 2 + 3", "2. Then multiply the result by 4"]
                User: Next step?
                Assistant: FUNCTION_CALL: {"name":"calculate","args":{"expression":"2 + 3"}}
                User: Result is 5. Let's verify this step.
                Assistant: FUNCTION_CALL: {"name":"verify","args":{"expression":"2 + 3","expected":5}}
                User: Verified. Next step?
                Assistant: FUNCTION_CALL: {"name":"calculate","args":{"expression":"5 * 4"}}
                User: Result is 20. Let's verify the final answer.
                Assistant: FUNCTION_CALL: {"name":"verify","args":{"expression":"(2 + 3) * 4","expected":20}}
                User: Verified correct.
                Assistant: FINAL_ANSWER: [20]"""

                problem = "(23 + 7) * (15 - 8) * (12.5/25.0)"
                # problem = """Get the ASCII values of all characters in the word "INDIA", then compute the sum of exponentials of those ASCII values."""

                console.print(Panel(f"Problem: {problem}", border_style="cyan"))

                # Initialize conversation
                prompt = f"{system_prompt}\n\nSolve this problem step by step: {problem}"
                conversation_history = []

                while True:
                    response = await generate_with_timeout(client, prompt)
                    if not response or not response.text:
                        break

                    result = response.text.strip()
                    console.print(f"\n[yellow]Assistant:[/yellow] {result}")

                    if result.startswith("FUNCTION_CALL:"):
                        # Validate JSON first
                        is_valid, parsed_json, validation_message = validate_json(result)
                        
                        try:
                            if parsed_json:
                                func_name = parsed_json["name"]
                                args = parsed_json["args"]
                                
                                if func_name == "show_reasoning":
                                    try:
                                        steps = args.get("steps", [])
                                        await session.call_tool("show_reasoning", arguments={"steps": steps})
                                        prompt += f"\nUser: Next step?"
                                    except Exception as e:
                                        prompt += await handle_tool_error(
                                            session, 
                                            str(e), 
                                            f"show_reasoning with steps: {steps}"
                                        )
                                        
                                elif func_name == "calculate":
                                    try:
                                        expression = args.get("expression", "")
                                        calc_result = await session.call_tool("calculate", arguments={"expression": expression})
                                        
                                        if calc_result.content:
                                            value = calc_result.content[0].text
                                            
                                            # Self-check with fallback
                                            try:
                                                self_check_prompt = f"""Given the calculation:
                                                Expression: {expression}
                                                Result: {value}
                                                
                                                Is the result reasonable?

                                                Respond with ONLY 'YES' if all checks pass, or explain why they don't pass.
                                                """
                                                
                                                self_check_response = await get_llm_response(client, self_check_prompt)
                                                
                                                if not self_check_response:
                                                    prompt += await handle_tool_error(
                                                        session,
                                                        "Self-check failed to respond",
                                                        f"self-check for calculation: {expression} = {value}"
                                                    )
                                                elif self_check_response.strip() != "YES":
                                                    # Call fallback but continue with verification
                                                    await session.call_tool("fallback_reasoning", arguments={
                                                        "step_description": f"Self-check concerns: {self_check_response}"
                                                    })
                                            
                                            except Exception as e:
                                                prompt += await handle_tool_error(
                                                    session,
                                                    str(e),
                                                    f"self-check for calculation: {expression}"
                                                )
                                            
                                            prompt += f"\nUser: Result is {value}. Let's verify this step."
                                            conversation_history.append((expression, float(value)))
                                        else:
                                            prompt += await handle_tool_error(
                                                session,
                                                "No calculation result returned",
                                                f"calculate: {expression}"
                                            )
                                            
                                    except Exception as e:
                                        prompt += await handle_tool_error(
                                            session,
                                            str(e),
                                            f"calculate: {expression}"
                                        )
                                        
                                elif func_name == "verify":
                                    try:
                                        expression = args.get("expression", "")
                                        expected = float(args.get("expected", 0))
                                        verify_result = await session.call_tool("verify", arguments={
                                            "expression": expression,
                                            "expected": expected
                                        })
                                        
                                        if verify_result.content and verify_result.content[0].text.lower() == "false":
                                            # Verification failed, trigger fallback
                                            await session.call_tool("fallback_reasoning", arguments={
                                                "step_description": f"Verification failed for {expression} = {expected}"
                                            })
                                        
                                        prompt += f"\nUser: Verification completed. Next step?"
                                        
                                    except Exception as e:
                                        prompt += await handle_tool_error(
                                            session,
                                            str(e),
                                            f"verify: {expression} = {expected}"
                                        )
                                    
                                elif func_name == "fallback_reasoning":
                                    # Direct fallback call from LLM
                                    try:
                                        step_description = args.get("step_description", "")
                                        await session.call_tool("fallback_reasoning", arguments={
                                            "step_description": step_description
                                        })
                                        prompt += "\nUser: Fallback processed. Please proceed with an alternative approach."
                                    except Exception as e:
                                        console.print(f"[red]Error in fallback handling: {e}[/red]")
                                
                        except Exception as e:
                            prompt += await handle_tool_error(
                                session,
                                str(e),
                                "general tool execution"
                            )

                    elif result.startswith("FINAL_ANSWER:"):
                        # Verify the final answer against the original problem
                        if conversation_history:
                            final_answer = float(result.split("[")[1].split("]")[0])
                            await session.call_tool("verify", arguments={
                                "expression": problem,
                                "expected": final_answer
                            })
                        break
                    
                    prompt += f"\nAssistant: {result}"

                console.print("\n[green]Calculation completed![/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    asyncio.run(main())
