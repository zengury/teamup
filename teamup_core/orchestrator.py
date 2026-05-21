"""编排器 — 唐僧 + 四徒弟自动协作 + 状态机"""

from __future__ import annotations

from typing import AsyncIterator, Callable

from .agent import Agent
from .config import get_agent_name
from .llm import _strip_invoke
from .session import Session

import logging
log = logging.getLogger("teamup.orchestrator")


class Orchestrator:
    """管理整个取经团队，自动推进，状态持久化。"""

    def __init__(self, session: Session):
        self.session = session
        self.workspace = str(session.workspace)
        self.memory = session.read_memory()
        self._tangseng_history: list[dict] = session.load_history()
        self._state = session.get_state()

    async def run_turn(
        self,
        user_message: str,
        on_event: Callable,
    ) -> str:
        all_output: list[str] = []

        # 推送当前状态给前端
        await on_event("session_state", state=self._state)

        # 第一轮：用户消息 → 唐僧开始干活
        await on_event("agent_status", agent="唐僧", status="thinking", activity="理解需求")

        text = await self._ask_tangseng(user_message, on_event)
        all_output.append(text)

        # 自主推进：根据状态机缺啥补啥
        for i in range(5):
            if self._state.get("stage") == "done":
                break

            await on_event("agent_status", agent="唐僧", status="thinking", activity=f"自动推进 {i+1}/5")

            prompt = self._build_progress_prompt()
            text = await self._ask_tangseng(prompt, on_event)
            all_output.append(text)

            if "全部交付完成" in text:
                self._state["stage"] = "done"
                self.session.save_state(self._state)
                break

        # 保存
        final = "\n\n".join(t for t in all_output if t)
        self._tangseng_history.append({"role": "user", "content": user_message})
        self._tangseng_history.append({"role": "assistant", "content": final[:5000]})
        if len(self._tangseng_history) > 20:
            self._tangseng_history = self._tangseng_history[-20:]
        self.session.save_history(self._tangseng_history)

        self.session.write_memory(
            f"需求: {user_message[:200]}\n"
            f"阶段: {self._state.get('stage', '?')}\n"
            f"产出: {[f['name'] for f in self.session.get_files()]}"
        )

        await on_event("session_state", state=self._state)

        files = self.session.get_files()
        if files:
            await on_event("files_updated", files=files)

        return final

    def _build_progress_prompt(self) -> str:
        """根据当前状态生成进度检查提示。"""
        stage = self._state.get("stage", "init")
        completed = self._state.get("completed", [])
        STAGE_NEXT = {
            "init": "委派八戒写PRD到outputs/",
            "prd": "委派猴哥写技术方案+代码到outputs/",
            "tech_spec": "委派猴哥写代码到outputs/",
            "code": "委派沙僧写测试+白龙马做客户成功方案",
            "test": "委派白龙马做客户成功方案",
            "customer_success": "回复「✅ 全部交付完成」",
        }
        next_action = STAGE_NEXT.get(stage, "回复「✅ 全部交付完成」")

        return (
            f"当前阶段：{stage}，已完成：{completed}。\n"
            f"下一步：{next_action}。\n"
            f"立即执行，做完后用glob('outputs/*')确认产出。"
        )

    def _advance_stage(self, new_stage: str) -> None:
        """推进状态机。"""
        completed = self._state.get("completed", [])
        current = self._state.get("stage", "init")
        if current not in completed and current != "init":
            completed.append(current)
        self._state["stage"] = new_stage
        self._state["completed"] = completed
        self.session.save_state(self._state)

    async def _ask_tangseng(self, message: str, on_event: Callable) -> str:
        tangseng = Agent(role="tangseng", workspace=self.workspace, memory_context=self.memory)
        return await tangseng.chat_stream_loop(
            user_message=message,
            history=self._tangseng_history,
            on_event=on_event,
            on_delegate=self._make_delegate(on_event),
        )

    def _make_delegate(self, on_event: Callable):
        async def handle_delegate(args: dict) -> str:
            sub_role = (args.get("agent") or "").strip()
            task = (args.get("task") or "").strip()

            ROLE_MAP = {
                "bajie": "bajie", "八戒": "bajie",
                "wukong": "wukong", "猴哥": "wukong",
                "shawujing": "shawujing", "沙僧": "shawujing",
                "bailongma": "bailongma", "白龙马": "bailongma",
            }
            sub_role = ROLE_MAP.get(sub_role.lower(), sub_role)

            if sub_role not in {"bajie", "wukong", "shawujing", "bailongma"}:
                return f"无效角色: {args.get('agent','')}"

            if not task:
                return "任务不能为空"

            sub_name = get_agent_name(sub_role)
            log.info(f"委派 {sub_name}: {task[:80]}...")

            await on_event("thread_created", agent=sub_name)
            await on_event("delegation", from_agent="唐僧", to_agent=sub_name, text=task)
            await on_event("agent_status", agent="唐僧", status="delegating", activity=f"→ {sub_name}")
            await on_event("agent_status", agent=sub_name, status="working", activity=task[:40] or "执行中")

            sub_agent = Agent(role=sub_role, workspace=self.workspace, memory_context=self.memory)
            result = await sub_agent.run_task(task)
            result = _strip_invoke(result)

            # 状态推进
            STAGE_MAP = {
                "bajie": "prd",
                "wukong": "code",
                "shawujing": "test",
                "bailongma": "customer_success",
            }
            new_stage = STAGE_MAP.get(sub_role, self._state.get("stage", "init"))
            self._advance_stage(new_stage)

            await on_event("session_state", state=self._state)

            preview = result[:200].replace("\n", " ")
            await on_event("delegation_reply", from_agent=sub_name, to_agent="唐僧", text=preview)
            await on_event("agent_status", agent=sub_name, status="delivered", activity="已交付")
            await on_event("agent_status", agent="唐僧", status="thinking", activity=f"接收 {sub_name}")

            return result

        return handle_delegate
