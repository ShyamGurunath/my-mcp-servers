import json

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from openai import OpenAI
import asyncio
from typing import List, Dict, Any

# Assuming ClientSession and streamablehttp_client are defined elsewhere and work as shown

# Placeholder for messages, will be populated in the loop
messages = []

# --- Hypothetical function to search your MCP resources ---
async def search_mcp_resources(session, query: str) -> List[str]:
    """
    Searches through MCP resources based on the query.
    This is a placeholder; your actual MCP might have a more sophisticated search.
    """
    all_resources = await session.list_resources()
    relevant_content = []
    # Simple keyword matching for demonstration
    for resource in all_resources.resources: # Assuming 'resources' is an attribute of the response
        if query.lower() in resource.name.lower() or \
           (hasattr(resource, 'content') and query.lower() in resource.content.lower()):
            if hasattr(resource, 'content'):
                relevant_content.append(resource.content)
            elif hasattr(resource, 'description'): # Or whatever attribute holds the actual data
                 relevant_content.append(resource.description)
    return relevant_content

# --- Hypothetical function to get a specific prompt from MCP ---
async def get_mcp_prompt(session, prompt_name: str) -> str:
    """
    Retrieves a specific prompt template from MCP.
    """
    # Assuming list_prompts() returns prompts with a 'name' and 'template' or 'content' field
    all_prompts = await session.list_prompts()
    for prompt in all_prompts.prompts: # Assuming 'prompts' is an attribute of the response
        if prompt.name == prompt_name:
            return prompt.template if hasattr(prompt, 'template') else prompt.content
    return None

async def main():
    async with (streamablehttp_client(url="http://0.0.0.0:8003/mcp") as (read, write, _),
                streamablehttp_client(url="http://0.0.0.0:8003/mcp") as (read_1, write_1, w)):
        async with (ClientSession(read, write) as session, ClientSession(read_1, write_1) as session_1):

            await session.initialize()
            await session_1.initialize()

            list_tool = await session.list_tools()
            list_resources = await session.list_resources()
            list_prompts = await session.list_prompts() # Fetch prompts

            print("Available Resources:", list_resources)
            print("Available Prompts:", list_prompts)


            tools = [{
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            } for tool in list_tool.tools]
            print("Configured Tools:", tools)

            client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

            # Initialize messages outside the loop
            global messages
            messages = []

            while True:
                inp = input("Enter your message: ")
                if inp == "exit":
                    break
                if inp == "clear":
                    messages = []
                    print("Conversation cleared.")
                    continue

                # --- RAG Integration: Dynamically add resource context ---
                # This is a very simple trigger. You'd likely use more sophisticated logic
                # or a dedicated RAG pipeline.
                resource_context = ""
                if "tell me about" in inp.lower() or "what is" in inp.lower():
                    # Extract a keyword from the input, e.g., "cpu usage" or "ram usage"
                    # For a real system, you'd use NLP to extract entities.
                    if "cpu usage" in inp.lower():
                        resource_query = "cpu usage"
                    elif "ram usage" in inp.lower():
                        resource_query = "ram usage"
                    else:
                        resource_query = inp # Fallback to full input

                    relevant_data = await search_mcp_resources(session, resource_query)
                    if relevant_data:
                        resource_context = "\n\nRelevant Information from Resources:\n" + "\n".join(relevant_data)

                # --- Prompt Management Integration: Dynamically set system prompt ---
                # You could have different system prompts for different conversation types.
                # Example: If the user explicitly asks for a "friendly chat"
                system_prompt_content = ""
                if "friendly chat" in inp.lower() and "friendly_assistant_prompt" in [p.name for p in list_prompts.prompts]: # Check if prompt exists
                    system_prompt_content = await get_mcp_prompt(session, "friendly_assistant_prompt")
                    # If we set a new system prompt, it should ideally be at the beginning of messages
                    # This demonstrates how you might dynamically change the system prompt.
                    # For a continuous conversation, you might need to manage how system messages
                    # are added to avoid repetition or conflicting instructions.
                    if system_prompt_content and not any(m['role'] == 'system' and m['content'] == system_prompt_content for m in messages):
                         messages.insert(0, {"role": "system", "content": system_prompt_content})
                         print(f"Applying custom system prompt: {system_prompt_content[:50]}...")


                current_user_message = {"role": "user", "content": inp + resource_context}
                messages.append(current_user_message)

                resp = client.chat.completions.create(
                    model="llama3.1:8b",
                    messages=messages,
                    tools=tools,
                    tool_choice="auto"
                )

                # Update messages with the assistant's response (tool call or content)
                assistant_response_message = resp.choices[0].message
                messages.append(assistant_response_message)
                print(f"Assistant: {assistant_response_message}")

                if assistant_response_message.tool_calls:
                    for execution in assistant_response_message.tool_calls:
                        tool_name = execution.function.name
                        tool_arguments = json.loads(execution.function.arguments)
                        print(f"Calling tool: {tool_name} with arguments: {tool_arguments}")

                        result = await session.call_tool(name=tool_name, arguments=tool_arguments)
                        print(f"Tool result: {result}")

                        # Append tool output back to messages for the model's next turn
                        messages.append({
                            "role": "tool",
                            "tool_call_id": execution.id, # Important for OpenAI API
                            "name": tool_name,
                            "content": json.dumps(result.content[0].text) # Assuming result.content is serializable
                        })

                        # Get another response from the model with the tool output
                        second_resp = client.chat.completions.create(
                            model="llama3.1:8b",
                            messages=messages,
                            tools=tools, # Keep tools available
                            tool_choice="auto"
                        )
                        second_assistant_response = second_resp.choices[0].message
                        messages.append(second_assistant_response)
                        print(f"Assistant (after tool): {second_assistant_response.content}")

                else:
                    print(f"My Assistant resp : {assistant_response_message.content}")
                    # If no tool call, the assistant's content is the final response for this turn.
                    # This is already covered by `messages.append(assistant_response_message)`
                    pass

if __name__ == "__main__":
    asyncio.run(main())