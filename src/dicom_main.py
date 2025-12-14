# main.py
from agent.planner import PlannerAgent
from agent.executor import ExecutorAgent
from tools.download_tool import DownloadTool
from tools.metadata_tool import MetadataTool
from tools.vector_tool import VectorStoreTool

def main():
    tools = {
        "download_files": DownloadTool(),
        "extract_metadata": MetadataTool(),
        "create_vector_store": VectorStoreTool(),
    }

    planner = PlannerAgent()
    executor = ExecutorAgent(tools)

    goal = "Download DICOM files, extract metadata, and build a vector database"

    plan = planner.plan(goal)
    result = executor.execute(plan)

    if result:
        #print(result)
        print(f"Final vector store contains {len(result.get('vector_store', []))} entries.")


if __name__ == "__main__":
    main()
