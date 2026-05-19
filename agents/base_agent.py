from pathlib import Path
from providers import get_provider


class BaseAgent:
    def __init__(self, role: str):
        self.role = role
        self.provider = get_provider(role)
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        prompt_file = Path("prompts") / f"{self.role}.md"
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        return f"You are {self.role}, an AI assistant."

    def describe(self) -> str:
        return f"{self.role} [{self.provider.describe()}]"

    def run(self, task: str, context: str = "") -> str:
        user_message = task
        if context:
            user_message = f"## 背景信息\n\n{context}\n\n## 任务\n\n{task}"

        chunks = []
        for text in self.provider.stream(self.system_prompt, user_message):
            print(text, end="", flush=True)
            chunks.append(text)
        print()
        return "".join(chunks)
