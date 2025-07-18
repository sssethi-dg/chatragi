"""
ChatRagi CLI Interface

Allows users to interact with the local chatbot using different persona tones.
"""

from chatragi.utils.chatbot import ask_bot


def main():
    """
    Launches a CLI-based chat loop allowing persona selection per question.
    """
    print("🧠 ChatRagi CLI — Now with Personas!")
    print("Available Personas: default | professional | witty")
    print("Type 'exit' anytime to quit.\n")

    while True:
        # Capture user input
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("\n👋 Goodbye!")
            break

        # Capture persona selection
        persona_input = (
            input("Choose a persona (default/professional/witty): ")
            .strip()
            .lower()
        )
        persona = (
            persona_input
            if persona_input in {"default", "professional", "witty"}
            else "default"
        )

        # Send to chatbot and display response
        try:
            response = ask_bot(user_input=user_input, persona=persona)
            print(f"\nChatRagi ({persona.capitalize()} Tone):\n{response}\n")
        except Exception as e:
            print(f"\n[Error] {e}\n")


if __name__ == "__main__":
    main()
