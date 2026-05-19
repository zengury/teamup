import anthropic
from pathlib import Path
import config


class BaseAgent:
    def __init__(self, role: str):
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.role = role
        self.model = config.AGENT_MODELS.get(role, "claude-opus-4-7")
        self.max_tokens = config.MAX_TOKENS.get(role, 8192)
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        prompt_file = Path("prompts") / f"{self.role}.md"
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        return f"You are {self.role}, an AI assistant."

    def run(self, task: str, context: str = "") -> str:
        user_message = task
        if context:
            user_message = f"## 背景信息\n\n{context}\n\n## 任务\n\n{task}"

        system_content = [
            {
                "type": "text",
                "text": self.system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]

        create_kwargs: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system_content,
            "messages": [{"role": "user", "content": user_message}],
        }

        if self.model == "claude-opus-4-7":
            create_kwargs["thinking"] = {"type": "adaptive"}

        full_text = []
        with self.client.messages.stream(**create_kwargs) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
                full_text.append(text)

        print()
        return "".join(full_text)
