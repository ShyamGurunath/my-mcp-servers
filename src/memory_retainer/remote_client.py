from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

resp = client.chat.completions.create(
    model="llama3.1:8b",
    messages=[
        {"role": "user", "content": "tell me about my cpu usage & ram usage of my device ?"}
    ],
    tools=[
        {
            "type": "mcp",
            "server_label": "system_info",
            "server_url": "http://0.0.0.0:8003/mcp",
            "require_approval": "never",
        },
    ],
    tool_choice="auto"
)
print(resp)
