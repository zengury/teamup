let idCounter = 0;
const nextId = (prefix) => `${prefix}_${++idCounter}`;
export class InMemoryHarnessStore {
    artifacts = new Map();
    runs = new Map();
    events = [];
    approvals = [];
    seedArtifact(artifact) {
        const saved = {
            ...artifact,
            id: nextId("artifact"),
            createdAt: new Date().toISOString()
        };
        this.artifacts.set(saved.id, saved);
        return saved;
    }
    async createRun(input) {
        const run = { ...input, id: nextId("run"), status: "queued" };
        this.runs.set(run.id, run);
        return { id: run.id };
    }
    async updateRun(id, patch) {
        this.runs.set(id, { ...(this.runs.get(id) ?? {}), ...patch });
    }
    async getArtifacts(ids) {
        return ids.map((id) => this.artifacts.get(id)).filter((artifact) => Boolean(artifact));
    }
    async saveArtifact(artifact) {
        return this.seedArtifact(artifact);
    }
    async saveApproval(runId, approval) {
        this.approvals.push({ runId, approval });
    }
    async emitEvent(event) {
        this.events.push(event);
    }
}
export class MockModelAdapter {
    async complete(input) {
        if (input.context.agentName === "bailongma") {
            return {
                artifacts: [
                    {
                        kind: "customer_feedback_summary",
                        title: "Daily customer feedback summary",
                        body: {
                            sentiment: "neutral-positive",
                            blockers: ["Customer has not confirmed the Stitch prototype yet"],
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
