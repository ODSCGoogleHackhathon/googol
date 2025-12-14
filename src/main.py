from agent.agent import Agent

def main():
    agent = Agent()
    print("Gemini ReAct Agent (type exit to quit)")
    while True:
        q = input("User: ")
        if q.lower() in ("exit", "quit"):
            break
        answer, trace = agent.run(q)
        print("\n--- ReAct Trace ---")
        for t in trace:
            print(t)
        print("\nAgent:", answer)

if __name__ == "__main__":
    main()
