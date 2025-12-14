from core.planner import Planner
from core.executor import Executor
from core.memory import VectorMemory

class Agent:
    def __init__(self):
        self.planner = Planner()
        self.executor = Executor()
        self.memory = VectorMemory()

    def run(self, user_input):
        plan = self.planner.create_plan(user_input)
        answer, trace = self.executor.execute(plan, self.memory, user_input)
        return answer, trace
