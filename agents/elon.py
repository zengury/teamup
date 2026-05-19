import json
import anthropic
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

import config
from tools.project_manager import save_note, read_note, list_files
from agents.jobs import JobsAgent
from agents.linux import LinuxAgent
from agents.turing import TuringAgent
from agents.bezos import BezosAgent

console = Console()

TOOLS = [
    {
        "name": "brief_jobs",
        "description": "委派 Jobs（产品经理）完成产品类任务，例如撰写 PRD、用户故事、功能规格。",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "给 Jobs 的任务描述，需清楚说明要交付什么文档及具体要求。",
                },
                "context": {
                    "type": "string",
                    "description": "给 Jobs 的背景信息，例如客户业务描述、已确认的需求等。",
                },
            },
            "required": ["task"],
        },
    },
    {
        "name": "brief_linux",
        "description": "委派 Linux（软件工程师）完成技术类任务，例如编写代码、设计技术方案、提供集成指南。",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "给 Linux 的任务描述，需清楚说明要实现什么功能和技术要求。",
                },
                "context": {
                    "type": "string",
                    "description": "给 Linux 的背景信息，例如 PRD、技术约束、已有代码结构等。",
                },
            },
            "required": ["task"],
        },
    },
    {
        "name": "brief_turing",
        "description": "委派 Turing（QA工程师）完成测试类任务，例如制定测试计划、编写测试用例、分析边缘情况。",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "给 Turing 的任务描述，需清楚说明要测试的功能范围。",
                },
                "context": {
                    "type": "string",
                    "description": "给 Turing 的背景信息，例如 PRD、代码实现、验收标准等。",
                },
            },
            "required": ["task"],
        },
    },
    {
        "name": "brief_bezos",
        "description": "委派 Bezos（客户成功经理）完成客户成功类任务，例如制定 KPI 框架、成功计划、引导方案、ROI 测算。",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "给 Bezos 的任务描述，需清楚说明要交付什么客户成功材料。",
                },
                "context": {
                    "type": "string",
                    "description": "给 Bezos 的背景信息，例如客户业务背景、产品功能、目标用户等。",
                },
            },
            "required": ["task"],
        },
    },
    {
        "name": "save_project_note",
        "description": "将交付物或重要信息保存到当前项目目录中，以 Markdown 文件格式存储。",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "文件名（不含路径），例如 'PRD'、'test_plan'、'architecture'。",
                },
                "content": {
                    "type": "string",
                    "description": "要保存的内容（Markdown 格式）。",
                },
            },
            "required": ["filename", "content"],
        },
    },
    {
        "name": "read_project_note",
        "description": "读取当前项目目录中已保存的文件内容。",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "要读取的文件名（不含路径）。",
                },
            },
            "required": ["filename"],
        },
    },
    {
        "name": "list_project_files",
        "description": "列出当前项目目录中所有已保存的文件。",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


def _execute_tool(tool_name: str, tool_input: dict, project_name: str) -> str:
    if tool_name == "brief_jobs":
        console.print(Panel("[bold cyan]📋 Jobs 正在工作...[/bold cyan]", border_style="cyan"))
        agent = JobsAgent()
        result = agent.run(tool_input["task"], tool_input.get("context", ""))
        save_note(project_name, "PRD", result)
        return result

    elif tool_name == "brief_linux":
        console.print(Panel("[bold green]💻 Linux 正在工作...[/bold green]", border_style="green"))
        agent = LinuxAgent()
        result = agent.run(tool_input["task"], tool_input.get("context", ""))
        save_note(project_name, "implementation", result)
        return result

    elif tool_name == "brief_turing":
        console.print(Panel("[bold yellow]🧪 Turing 正在工作...[/bold yellow]", border_style="yellow"))
        agent = TuringAgent()
        result = agent.run(tool_input["task"], tool_input.get("context", ""))
        save_note(project_name, "test_plan", result)
        return result

    elif tool_name == "brief_bezos":
        console.print(Panel("[bold magenta]📈 Bezos 正在工作...[/bold magenta]", border_style="magenta"))
        agent = BezosAgent()
        result = agent.run(tool_input["task"], tool_input.get("context", ""))
        save_note(project_name, "success_plan", result)
        return result

    elif tool_name == "save_project_note":
        filepath = save_note(project_name, tool_input["filename"], tool_input["content"])
        return f"已保存到: {filepath}"

    elif tool_name == "read_project_note":
        return read_note(project_name, tool_input["filename"])

    elif tool_name == "list_project_files":
        files = list_files(project_name)
        if not files:
            return "当前项目目录为空。"
        return "项目文件列表:\n" + "\n".join(f"- {f}" for f in files)

    else:
        return f"[未知工具: {tool_name}]"


class ElonAgent:
    def __init__(self, project_name: str = "default"):
        cfg = config.get_agent_config("elon")
        if cfg.get("provider", "anthropic") != "anthropic":
            raise ValueError(
                "Elon 必须使用 anthropic provider（需要 tool use + adaptive thinking）。"
                "请在 agents_config.yaml 中将 elon.provider 设置为 anthropic。"
            )
        api_key_env = cfg.get("api_key_env", "ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=config.get_api_key(api_key_env))
        self.model = cfg["model"]
        self.max_tokens = cfg.get("max_tokens", 16384)
        self.thinking_mode = cfg.get("thinking", "adaptive")
        self.project_name = project_name
        self.history: list[dict] = []
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        prompt_file = Path("prompts/elon.md")
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        return "You are Elon, the CEO of an AI delivery team."

    def set_project(self, project_name: str) -> None:
        self.project_name = project_name
        self.history = []

    def chat(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})

        system_content = [
            {
                "type": "text",
                "text": self.system_prompt + f"\n\n## 当前项目\n\n项目名称: {self.project_name}",
                "cache_control": {"type": "ephemeral"},
            }
        ]

        create_kwargs: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system_content,
            "tools": TOOLS,
        }
        if self.thinking_mode == "adaptive":
            create_kwargs["thinking"] = {"type": "adaptive"}
        elif isinstance(self.thinking_mode, dict):
            create_kwargs["thinking"] = self.thinking_mode

        while True:
            response = self.client.messages.create(
                messages=self.history,
                **create_kwargs,
            )

            self.history.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                text_blocks = [
                    block.text for block in response.content if hasattr(block, "type") and block.type == "text"
                ]
                return "\n".join(text_blocks)

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if not (hasattr(block, "type") and block.type == "tool_use"):
                        continue

                    tool_name = block.name
                    tool_input = block.input
                    tool_use_id = block.id

                    console.print(f"\n[dim]→ 调用工具: {tool_name}[/dim]")

                    result = _execute_tool(tool_name, tool_input, self.project_name)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": result,
                        }
                    )

                self.history.append({"role": "user", "content": tool_results})
            else:
                text_blocks = [
                    block.text for block in response.content if hasattr(block, "type") and block.type == "text"
                ]
                return "\n".join(text_blocks)
