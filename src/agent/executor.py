# agents/executor.py
class ExecutorAgent:
    def __init__(self, tools: dict):
        self.tools = tools
        self.context = {}

    def resolve_args(self, args: dict):
        resolved = {}
        for k, v in args.items():
            if isinstance(v, str) and v.startswith("$previous."):
                key = v.replace("$previous.", "")
                resolved[k] = self.context.get(key)
            else:
                resolved[k] = v
        return resolved

    def execute(self, plan: dict):
        for step in plan["steps"]:
            tool_name = step["tool"]
            tool = self.tools[tool_name]

            args = self.resolve_args(step["args"])
            result = tool.run(**args)

            # Save outputs for downstream steps
            self.context.update(result)

        return self.context
