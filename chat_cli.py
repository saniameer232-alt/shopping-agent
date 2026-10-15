from src.agent import ShoppingAgent

agent = ShoppingAgent()
print("Shopping Agent ready. Type 'quit' to exit.\n")
while True:
    msg = input("You: ").strip()
    if msg.lower() in ("quit", "exit"):
        break
    print("\nAgent:", agent.chat(msg), "\n")