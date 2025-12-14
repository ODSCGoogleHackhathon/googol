from typing import List


class EvalCase:
    def __init__(self, prompt, expected_keywords: List[str]):
        self.prompt = prompt
        self.expected_keywords = expected_keywords


    class Evaluator:
        def run(self, agent, cases: List[EvalCase]):
            results = []
            for case in cases:
                response = agent(case.prompt)
                score = sum(1 for k in case.expected_keywords if k in response.lower())
                results.append({
                "prompt": case.prompt,
                "score": score,
                "response": response
                })
            return results