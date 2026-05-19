from pathlib import Path
from datetime import datetime
import config


def get_project_dir(project_name: str) -> Path:
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in project_name)
    project_dir = config.PROJECTS_DIR / safe_name
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir


def save_note(project_name: str, filename: str, content: str) -> str:
    project_dir = get_project_dir(project_name)
    if not filename.endswith(".md"):
        filename = filename + ".md"
    filepath = project_dir / filename
    filepath.write_text(content, encoding="utf-8")
    return str(filepath)


def read_note(project_name: str, filename: str) -> str:
    project_dir = get_project_dir(project_name)
    if not filename.endswith(".md"):
        filename = filename + ".md"
    filepath = project_dir / filename
    if not filepath.exists():
        return f"[文件不存在: {filename}]"
    return filepath.read_text(encoding="utf-8")


def list_files(project_name: str) -> list[str]:
    project_dir = get_project_dir(project_name)
    return [f.name for f in sorted(project_dir.iterdir()) if f.is_file()]


def list_projects() -> list[str]:
    return [d.name for d in sorted(config.PROJECTS_DIR.iterdir()) if d.is_dir()]


def save_conversation_history(project_name: str, history: list[dict]) -> None:
    import json
    project_dir = get_project_dir(project_name)
    history_file = project_dir / "conversation_history.json"
    simplified = []
    for msg in history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if isinstance(content, str):
            simplified.append({"role": role, "content": content})
        elif isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                elif hasattr(block, "type") and block.type == "text":
                    text_parts.append(block.text)
            simplified.append({"role": role, "content": "\n".join(text_parts)})
    history_file.write_text(json.dumps(simplified, ensure_ascii=False, indent=2), encoding="utf-8")


def load_conversation_history(project_name: str) -> list[dict]:
    import json
    project_dir = get_project_dir(project_name)
    history_file = project_dir / "conversation_history.json"
    if not history_file.exists():
        return []
    data = json.loads(history_file.read_text(encoding="utf-8"))
    return data
