import sys
import os

# Ensure orchestrator.py is importable
current_file = os.path.abspath(__file__)
project_root = current_file
while True:
    project_root = os.path.dirname(project_root)
    if os.path.isdir(os.path.join(project_root, 'services')):
        break
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from services.worker.worker.agents.orchestrator import chatbot_response

def main():
    print("\nSentinelAI Chatbot CLI (type 'quit' to exit)")
    conversation = []
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "quit":
            print("Exiting chatbot. Goodbye!")
            break
        conversation.append({"role": "user", "content": user_input})
        convo_dict = {"current_input": user_input, "history": conversation}
        result = chatbot_response(convo_dict)
        response = result.get("response", "[No response]")
        print(f"AI: {response}")
        conversation.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
