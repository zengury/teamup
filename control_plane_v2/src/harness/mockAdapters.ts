import type { AgentName, AgentOutput, Artifact, ContextPacket, HarnessStore, ModelAdapter } from "./types.js";

let idCounter = 0;
const nextId = (prefix: string) => `${prefix}_${++idCounter}`;

export class InMemoryHarnessStore implements HarnessStore {
  artifacts = new Map<string, Artifact>();
  runs = new Map<string, Record<string, unknown>>();
  events: unknown[] = [];
  approvals: unknown[] = [];

  seedArtifact(artifact: Omit<Artifact, "id" | "createdAt">) {
    const saved = {
      ...artifact,
      id: nextId("artifact"),
      createdAt: new Date().toISOString()
    };
    this.artifacts.set(saved.id, saved);
    return saved;
  }

  async createRun(input: {
    engagementId: Artifact["engagementId"];
    agentName: AgentName;
    triggerType: string;
    model: string;
  }) {
    const run = { ...input, id: nextId("run"), status: "queued" };
    this.runs.set(run.id, run);
    return { id: run.id };
  }

  async updateRun(id: string, patch: Record<string, unknown> & { status: string }) {
    this.runs.set(id, { ...(this.runs.get(id) ?? {}), ...patch });
  }

  async getArtifacts(ids: string[]) {
    return ids.map((id) => this.artifacts.get(id)).filter((artifact): artifact is Artifact => Boolean(artifact));
  }

  async saveArtifact(artifact: Omit<Artifact, "id" | "createdAt">) {
    return this.seedArtifact(artifact);
  }

  async saveApproval(runId: string, approval: Parameters<HarnessStore["saveApproval"]>[1]) {
    this.approvals.push({ runId, approval });
  }

  async emitEvent(event: Parameters<HarnessStore["emitEvent"]>[0]) {
    this.events.push(event);
  }
}

export class MockModelAdapter implements ModelAdapter {
  async complete(input: {
    model: string;
    systemPrompt: string;
    context: ContextPacket;
    triggerPayload: Record<string, unknown>;
  }): Promise<AgentOutput> {
    if (input.context.agentName === "bailongma") {
      return {
        artifacts: [
          {
            kind: "customer_feedback_summary",
            title: "Daily customer feedback summary",
            body: {
              sentiment: "neutral-positive",
              unresolvedInputs: ["Customer has not confirmed the Stitch prototype yet"],
              requestedChanges: ["Make store manager workflow lighter"],
              sourceFacts: input.context.facts
            }
          },
          {
            kind: "tangseng_feedback_brief",
            title: "Bai Longma to Tang Seng feedback brief",
            body: {
              recommendation: "Ask Bajie to simplify the first screen and ask Houge to delay noncritical analytics work.",
              urgency: "medium"
            }
          }
        ],
        events: [
          {
            type: "tangseng.customer_signal.received",
            payload: {
              sentiment: "neutral-positive",
              nextDecision: "adjust_prototype"
            }
          }
        ]
      };
    }

    return {
      artifacts: [
        {
          kind: "engagement_brief",
          title: "Mock engagement brief",
          body: {
            goal: "Turn conversation into a scoped SME agent pilot",
            sourceFacts: input.context.facts
          }
        }
      ],
      events: [
        {
          type: "bajie.product_idea.requested",
          payload: {
            reason: "Approved MVP needs a customer-visible prototype"
          }
        }
      ]
    };
  }
}
