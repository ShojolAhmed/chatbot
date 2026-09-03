import os
import json
from dotenv import load_dotenv
from openai import OpenAI, APIStatusError

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("BASE_URL")
)

# tools = [
#     {
#         "type": "function",
#         "function": {
#             "name": "get_current_directory",
#             "description": "Get the agent's current working directory.",
#             "parameters": {
#                 "type": "object",
#                 "properties": {},
#                 "required": []
#             }
#         }
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "change_directory",
#             "description": "Change the agent's current working directory.",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "path": {
#                         "type": "string",
#                         "description": "The directory path to change to."
#                     }
#                 },
#                 "required": ["path"]
#             }
#         }
#     }
# ]


# def get_current_directory():
#     return os.getcwd()


# def change_directory(path):
#     try:
#         os.chdir(path)
#         return f"Changed directory to: {os.getcwd()}"
#     except FileNotFoundError:
#         return f"Directory does not exist: {path}"
#     except NotADirectoryError:
#         return f"Not a directory: {path}"
#     except PermissionError:
#         return f"Permission denied: {path}"


MAX_RETRIES = 3
messages = []


def chat(user_input):
    messages.append({
        "role": "user",
        "content": user_input
    })

    for retry in range(MAX_RETRIES):
        try:
            while True:
                response = client.chat.completions.create(
                    model="claude-opus-5",
                    messages=messages,
                    # tools=tools,
                )

                message = response.choices[0].message

                if not message.tool_calls:
                    messages.append(message)
                    return message.content

                # messages.append(message)

                # for tool_call in message.tool_calls:
                #     name = tool_call.function.name
                #     args = json.loads(tool_call.function.arguments)

                #     if name == "get_current_directory":
                #         result = get_current_directory()
                #     elif name == "change_directory":
                #         result = change_directory(args["path"])
                #     else:
                #         result = f"Unknown tool: {name}"

                #     messages.append({
                #         "role": "tool",
                #         "tool_call_id": tool_call.id,
                #         "content": result,
                #     })

        except APIStatusError as e:
            if retry == MAX_RETRIES - 1:
                return f"Error {e.status_code}: {e.message}"

    return "Something went wrong."