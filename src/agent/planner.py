# agents/planner.py
class PlannerAgent:
    def plan(self, goal: str) -> dict:
        """
        Convert a goal into a structured execution plan
        """
        # In production, this is an LLM call
        return {
            "steps": [
                {
                    "tool": "download_files",
                    "args": {
                        "url": "https://example.com/dicom",
                        "output_dir": "data"
                    }
                },
                {
                    "tool": "extract_metadata",
                    "args": {
                        "files": "$previous.files"
                    }
                },
                {
                    "tool": "create_vector_store",
                    "args": {
                        "metadata": "$previous.metadata"
                    }
                }
            ]
        }
