import os
from pathlib import Path

project_name = "doctalk"

list_of_files = [
    # --- project root ---
    ".gitignore",
    ".env.example",
    "README.md",
    "pyproject.toml",
    "requirements.txt",
    "main.py",

    # --- configuration (read at runtime) ---
    "config/config.yaml",
    "params.yaml",

    # --- the installable package ---
    f"src/{project_name}/__init__.py",
    f"src/{project_name}/logger/__init__.py",
    f"src/{project_name}/exception/__init__.py",
    f"src/{project_name}/utils/__init__.py",
    f"src/{project_name}/utils/common.py",
    f"src/{project_name}/constants/__init__.py",
    f"src/{project_name}/entity/__init__.py",
    f"src/{project_name}/config/__init__.py",
    f"src/{project_name}/config/configuration.py",

    # --- components: each does one job ---
    f"src/{project_name}/components/__init__.py",
    f"src/{project_name}/components/data_ingestion.py",
    f"src/{project_name}/components/vector_store.py",
    f"src/{project_name}/components/retriever.py",
    f"src/{project_name}/components/agent_graph.py",

    # --- agent tools ---
    f"src/{project_name}/components/tools/__init__.py",
    f"src/{project_name}/components/tools/github_tool.py",
    f"src/{project_name}/components/tools/search_tool.py",
    f"src/{project_name}/components/tools/summarize_tool.py",

    # --- pipelines: orchestrate the components ---
    f"src/{project_name}/pipelines/__init__.py",
    f"src/{project_name}/pipelines/stage_01_ingestion.py",
    f"src/{project_name}/pipelines/stage_02_chat.py",

    # --- FastAPI layer ---
    "api/__init__.py",
    "api/routes.py",
    "api/schemas.py",

    # --- research notebooks ---
    "research/01_data_ingestion.ipynb",
    "research/02_vector_store.ipynb",
    "research/03_retriever.ipynb",
    "research/04_tools.ipynb",
    "research/05_agent_graph.ipynb",

    # --- evaluation ---
    "eval/qa_pairs.json",
    "eval/run_eval.py",

    # --- tests ---
    "tests/__init__.py",

    # --- frontend ---
    "ui/streamlit_app.py",
    ]

for filepath in list_of_files:
    filepath = Path(filepath)
    filedir, filename = os.path.split(filepath)

    if filedir != "":
        os.makedirs(filedir, exist_ok=True)
        print(f"Created directory: {filedir}")

    if not os.path.exists(filename):
        with open(filepath, "w") as f: 
            pass
        print(f"Created empty file: {filepath}")

    else:
        print(f"Already exists, skipped: {filepath}")