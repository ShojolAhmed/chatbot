messages = []


def add_message(role: str, content: str):
    messages.append(
        {
            "role": role,
            "content": content,
        }
    )


def get_messages():
    return messages


def clear_memory():
    messages.clear()
