class Planner:
    def create_plan(self, goal):
        return [
            {"thought": "User asked a question", "action": "analyze"},
            {"thought": "May need external info", "action": "search"},
            {"thought": "Answer using Gemini", "action": "final"}
        ]
