# Teamup Agent OS

一个面向 OPC / SME agent 交付业务的复杂平台原型。

当前版本是零依赖静态原型，首页已经是第一版西游取经 Agent Control Plane：

- 五个 agent 实时运行状态
- 唐僧 / 八戒 / 猴哥 / 沙僧 / 白龙马任务流转关系
- 顺序任务泳道与调整回路
- 产出内容列表
- 实时事件流
- 环节问题会自动回给上一环节和唐僧
- 唐僧编排后新增调度记录

直接在浏览器打开 `index.html` 即可体验。

关键工程文档：

- `ARCHITECTURE.md`: 产品与系统架构
- `HARNESS.md`: 每个 agent 的 harness 工程设计

Generic harness 代码：

- `src/orchestrator/journeyStateMachine.ts`: 取经状态机，消费 events 并输出 commands
- `src/orchestrator/collaborationLoop.ts`: 五个 agent 的持续迭代 loop 与学习信号
- `src/orchestrator/collaborationLoopExample.ts`: 打印协作 loop 和角色工具箱
- `src/orchestrator/stateSupervisor.ts`: 状态机监督层，发现异常转移并让唐僧介入
- `src/orchestrator/example.ts`: 状态机流转示例
- `src/orchestrator/supervisorExample.ts`: 状态机监督示例
- `src/harness/runAgent.ts`: generic harness 主流程
- `src/harness/trustHarness.ts`: 单环节可信度评分与多人协作可信度增强
- `src/harness/trustExample.ts`: 协作可信度从单点到 release-ready 的示例
- `src/harness/downstreamReviewExample.ts`: 下游完成自身环节后，回评上游产出质量的示例
- `src/harness/customerFeedback.ts`: 白龙马客户反馈采集、归一化和缺失反馈判断
- `src/harness/customerFeedbackExample.ts`: 白龙马如何把客户消息和使用指标转成唐僧 brief
- `src/harness/roleHarnessSpecs.ts`: 五个角色的输入门、输出门、信任门、交叉检查和失败路由
- `src/harness/roleHarnessExample.ts`: 打印每个角色 harness 方案
- `src/harness/toolCatalog.ts`: 每个角色的专业工具箱、风险级别和审批要求
- `src/harness/agentConfigs.ts`: 唐僧 / 八戒 / 猴哥 / 沙僧 / 白龙马配置
- `src/harness/mockAdapters.ts`: 内存 store 和 mock model adapter
- `src/harness/example.ts`: 白龙马定时反馈巡检示例
- `src/runtime/browserRuntime.ts`: 浏览器内可运行的本地项目引擎，把 founder 需求推进成真实项目状态、角色分工、产物和反馈
- `src/runtime/example.ts`: 本地项目引擎的端到端示例

本地验证：

```bash
npm install
npm run typecheck
npm run orchestrator:example
npm run supervisor:example
npm run loop:example
npm run trust:example
npm run downstream-review:example
npm run customer-feedback:example
npm run role-harness:example
npm run harness:example
npm run runtime:example
```

下一步建议升级为：

- Next.js 前端
- Postgres / Supabase 项目数据
- LangGraph / Temporal agent workflow
- 文件与录音 ingestion pipeline
- Eval 数据集与回归测试
- 客户门户与权限隔离
