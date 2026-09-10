from .chatbot import chat


def main():
    while True:
        user_input = input("You: ")
        if user_input in ("exit", "quit"):
            break

        response = chat(user_input)
        print("Bot:", response)


if __name__ == "__main__":
    main()
