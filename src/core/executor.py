from tools.gemini_client import GeminiClient
from tools.search_tool import SearchTool
from utils.logger import logger

class Executor:
    def __init__(self):
        self.llm = GeminiClient()
        self.search = SearchTool()

    def execute(self, plan, memory, user_input):
        reasoning_trace = []
        context = memory.retrieve(user_input)

        for step in plan:
            reasoning_trace.append(f"Thought: {step['thought']}")
            if step["action"] == "search":
                result = self.search.search(user_input)
                reasoning_trace.append(f"Observation: {result}")
                memory.store(result)

        prompt = f"""You are a ReAct-style agent.

Context:
{context}

Reasoning:
{chr(10).join(reasoning_trace)}

Question:
{user_input}

Provide final answer.
"""
        answer = self.llm.generate(prompt)
        memory.store(answer)
        return answer, reasoning_trace
