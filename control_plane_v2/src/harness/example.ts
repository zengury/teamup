import { agentConfigs } from "./agentConfigs.js";
import { InMemoryHarnessStore, MockModelAdapter } from "./mockAdapters.js";
import { runAgent } from "./runAgent.js";

async function main() {
  const store = new InMemoryHarnessStore();
  const model = new MockModelAdapter();

  const approvedBrief = store.seedArtifact({
    engagementId: "eng_001",
    kind: "engagement_brief",
    title: "Restaurant store inspection pilot",
    body: {
      goal: "Convert store inspection feedback into accountable remediation tasks",
      mvp: "Five-store pilot with human review"
    },
    status: "approved",
    createdByAgent: "tangseng",
    sourceArtifactIds: []
  });

  const result = await runAgent(agentConfigs.bailongma, {
    engagementId: "eng_001",
    agentName: "bailongma",
    triggerType: "bailongma.feedback_check.due",
    triggerPayload: {
      cadence: "daily",
      customerRespondedWithinSla: false
    },
    inputArtifactIds: [approvedBrief.id]
  }, {
    store,
    model
  });

  console.log(JSON.stringify({
    result,
    artifacts: Array.from(store.artifacts.values()),
    events: store.events,
    approvals: store.approvals
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  throw error;
});
