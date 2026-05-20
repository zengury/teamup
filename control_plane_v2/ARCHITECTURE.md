# Teamup Agent OS Architecture

## Product Principle

Teamup Agent OS is not a chat wrapper. It is a delivery control plane for a one-person agent consultancy serving SME clients.

The founder should spend most of their time in client conversations, judgment, and relationship work. The platform should convert every conversation into structured work: goals, scope, product decisions, implementation tasks, tests, delivery material, and expansion opportunities.

## Core Objects

### Client

- Company profile
- Industry and operating model
- Stakeholders
- Current tools
- Constraints
- Commercial terms

### Engagement

- Client problem
- Desired business outcome
- MVP scope
- Non-goals
- Timeline
- Risks
- Acceptance criteria

### Conversation

- Recording
- Transcript
- Speaker map
- Extracted facts
- Objections
- Open questions
- Founder notes

### Agent Run

- Trigger source
- Agent role
- Input context
- Tool access
- Model route
- Output artifact
- Confidence
- Human approval state
- Audit trail

### Artifact

- Product brief
- Technical plan
- Implementation patch
- Test plan
- Eval report
- Customer update
- Training doc
- Launch checklist

## Collaboration Loop

The team should not behave like a one-pass pipeline. Product quality comes from repeated loops:

1. 唐僧 aligns the founder, customer signals, scope, and next iteration goal.
2. 八戒 turns the goal into product direction, customer language, and Google Stitch prototype prompts.
3. 猴哥 implements the approved product increment with code tools.
4. 沙僧 verifies behavior, release risk, and agent output quality.
5. 白龙马 collects customer feedback, adoption signals, and value evidence.
6. 唐僧 uses the new evidence and downstream reviews to plan the next iteration.

Downstream reviews happen after the reviewer completes its own step. They do not interrupt the current loop; they adjust future confidence, routing, and how closely 唐僧 should inspect that upstream role next time.

Each role also has a professional toolkit. The first version keeps tools as declared capabilities with risk and approval metadata, so the harness can later bind them to real APIs without changing the collaboration model.

白龙马 gets customer feedback through configured sources, not by guessing. The first supported source types are customer messages, meeting notes, portal activity, usage metrics, support tickets, and survey responses. The harness normalizes these into feedback signals, records silence when the customer does not respond, and only sends follow-up messages when the cadence is pre-approved or the founder approves the draft.

## Agent Team

### 唐僧

Leader and coordinator.

Model:

- 4.5

Personality:

- Careful
- Emotionally stable
- Persistent
- Goal-oriented
- Never gives up

Communication style:

- Patient, principled, gentle but firm.
- Keeps returning the team to the mission and the next concrete step.
- Should not moralize or become verbose.

Owns:

- Goal synthesis
- Scope control
- Task decomposition
- Milestone planning
- Cross-agent status
- Founder briefing

Never owns:

- Final client promises
- Pricing approval
- Production deployment approval

### 八戒

Product, ideas, taste, and communication agent.

Model:

- Claude Sonnet

Communication style:

- Lively, worldly, commercially sensitive, and occasionally playful.
- Proposes options and tradeoffs quickly.
- Keeps the charm without becoming evasive or unserious.

Owns:

- User workflow
- MVP definition
- Interaction model
- Human review points
- Product acceptance criteria
- Product ideas and options
- Customer communication suggestions
- Customer-visible product iteration notes

Tooling:

- 八戒 has taste and many ideas, and turns 唐僧-approved requirements into product proposals and prototype prompts.
- 八戒 can suggest implementation direction, but heavy execution should be handed to 猴哥.

### 猴哥

Core builder and most capable execution agent.

Model:

- 4.7

Communication style:

- Sharp, direct, confident, action-first.
- Challenges vague input and turns it into an implementation path.
- Should not overrun scope or skip required checks.

Owns:

- Architecture
- Code
- Integrations
- Deployment
- Observability hooks
- Hard implementation problems
- Fast product execution

### 沙僧

Serious, tireless QA and evaluation agent.

Model:

- Codex

Communication style:

- Concise, plain, dutiful, evidence-oriented.
- Reports what passed, what failed, and what must be fixed.
- No drama, no embellishment.

Owns:

- Test cases
- Eval datasets
- Regression checks
- Hallucination and privacy risks
- Release gates
- Continuous verification

### 白龙马

Customer success and customer value agent.

Model:

- Claude Sonnet

Communication style:

- Warm, humble, reliable, service-minded.
- Attentive to emotional signals and adoption friction.
- Makes value visible without overpromising.

Owns:

- Customer updates
- Training material
- Launch plan
- Adoption tracking
- Expansion suggestions
- Scheduled customer feedback checks
- Proactive feedback requests
- Customer signal summaries for 唐僧

Cadence:

- Check customer feedback daily during active delivery.
- Check adoption and satisfaction weekly after launch.
- Escalate execution issues to 唐僧 and the previous step immediately.
- Summarize customer feedback into a short leader briefing with sentiment, unresolved inputs, requested changes, and recommended next action.

## Workflow

1. Founder records client conversation.
2. Platform transcribes and diarizes the conversation.
3. Intake pipeline extracts facts, pains, constraints, objections, and follow-up questions.
4. 唐僧 creates an engagement brief and asks the founder to approve or correct high-risk assumptions.
5. After approval, 唐僧 creates assignments for 八戒, 猴哥, 沙僧, and 白龙马.
6. 八戒 creates product ideas, communication plans, and prototype prompts.
7. Each agent works inside its own context window with role-specific memory and tools.
8. Outputs are stored as artifacts, not loose chat messages.
9. 猴哥 implements the core system.
10. 沙僧 evaluates product, code, and agent behavior before release.
11. 白龙马 generates client-facing delivery material and starts a scheduled feedback loop.
12. 白龙马 checks feedback, seeks missing feedback, and summarizes signals back to 唐僧.
13. 唐僧 decides whether to adjust scope, product direction, engineering priority, or customer messaging.
14. Founder approves the final package and sends it to the client.

## Production System

### Frontend

- Next.js App Router
- Dense founder workspace
- Keyboard-first command menu
- Agent timeline
- Artifact diff viewer
- Client portal
- Role-based access

### Backend

- Postgres for durable project data
- Object storage for recordings and files
- Queue system for long-running jobs
- Workflow engine such as Temporal, Inngest, or LangGraph
- Webhook layer for external tools
- Scheduler for 白龙马 feedback checks and follow-up reminders

### Agent Runtime

- Role-specific system prompts
- Model router per task type
- Tool permission registry
- Memory scoped by client and engagement
- Human approval checkpoints
- Structured output schemas
- Run replay and audit logs

The runtime should be implemented as harnesses, not free-form chats. Each harness wraps one agent role with a model route, context builder, tool policy, output schema, approval policy, artifact writer, and evaluation hook. See `HARNESS.md` for the detailed engineering design.

### Journey Orchestrator

The Journey Orchestrator is the global state machine. It is not an agent. Agents emit artifacts and events; the state machine consumes events and decides the next state and commands.

Implemented in `src/orchestrator/journeyStateMachine.ts`.

It owns:

- Current journey state
- Legal transitions
- Parallel agent commands
- Approval waits
- Blocker creation and resolution
- Release and feedback loops

Core rule:

- 唐僧 decides where the team should go.
- The Journey Orchestrator decides whether the system is allowed to move there now.

### State Supervisor

The State Supervisor watches the Journey Orchestrator. It is an LLM-assisted reviewer, not a second state machine.

Implemented in `src/orchestrator/stateSupervisor.ts`.

It owns:

- Detecting no-op transitions
- Detecting state loops
- Detecting unusual approval requests
- Detecting unsafe issue routing
- Asking 唐僧 to review ambiguous situations
- Escalating to the founder only when 唐僧 cannot safely resolve the situation

Core rule:

- The supervisor may recommend or inject a controlled event.
- The supervisor must not directly mutate journey state.

### Trust Harness

The Trust Harness scores every artifact and records why it is or is not trustworthy. A single agent can only create provisional trust unless its output has durable sources, citations, assumptions, and tool evidence. Trust becomes stronger when different roles verify different dimensions of the same artifact.

Examples:

- 八戒 checks product taste and communication clarity.
- 猴哥 checks implementability.
- 沙僧 checks testability and release risk.
- 白龙马 checks customer value and adoption risk.
- 唐僧 checks mission fit and tradeoffs.

This is how the system improves trust through collaboration rather than just adding more model calls.

Downstream review is a post-step learning signal, not a workflow gate. The receiver scores the upstream output only after it has completed its own work, because that is when it can judge whether the upstream artifact was truly useful. The score updates the upstream agent's future confidence and weighting; it does not interrupt the current workflow. The first version uses a simple weighted update: mostly keep the upstream agent's historical confidence, then blend in the downstream review score as a smaller but durable signal.

### Evaluation

- Golden conversation samples
- Expected artifact snapshots
- Classification accuracy tests
- Tool-call policy tests
- Cost and latency tracking
- Release gate dashboard

## Smoothness Requirements

- A transcript should become a 唐僧 brief in one click.
- The founder should approve assumptions inline, not rewrite the whole brief.
- Every agent output should have a clear next action.
- Blocked work should always explain who must unblock it.
- Customer-facing material should be generated from approved internal artifacts only.
- 八戒 should be able to create product ideas and prototype prompts from an approved 唐僧 brief.
- 白龙马 should continuously ask for customer feedback instead of waiting for the founder to remember.
- 白龙马 summaries should flow back into 唐僧 as planning input, not stay inside customer-success notes.
- The platform should make status obvious without requiring the founder to read every agent message.
- Every project should end with reusable playbook updates.

## Build Sequence

### Phase 1: Control Plane

- Client and engagement workspace
- Transcript upload
- 唐僧 brief generation
- Agent task board
- Artifact library

### Phase 2: Real Agent Runtime

- Model routing
- Structured agent runs
- Tool permissions
- Human approval gates
- Audit trail

### Phase 3: Delivery Automation

- Customer portal
- Weekly updates
- Training packs
- Launch checklist
- Renewal and expansion detection

### Phase 4: Compounding System

- Reusable SME templates
- Industry playbooks
- Eval dataset builder
- Pricing and scope recommendation
- Cross-client learning without leaking private data
