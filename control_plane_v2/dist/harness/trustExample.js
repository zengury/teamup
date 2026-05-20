import { agentConfigs } from "./agentConfigs.js";
import { amplifyCollaborativeTrust, assessArtifactTrust, trustGate } from "./trustHarness.js";
const context = {
    engagementId: "eng_001",
    agentName: "bajie",
    triggerType: "founder.approved",
    facts: ["engagement_brief: Restaurant store inspection pilot"],
    sourceArtifacts: [
        {
            id: "artifact_1",
            engagementId: "eng_001",
            kind: "engagement_brief",
            title: "Restaurant store inspection pilot",
            body: {},
            status: "approved",
            createdByAgent: "tangseng",
            sourceArtifactIds: [],
            createdAt: new Date().toISOString()
        }
    ],
    workingNotes: []
};
const artifact = {
    kind: "product_idea_brief",
    title: "Store manager remediation flow",
    body: {
        recommendation: "Make the first screen a daily remediation queue.",
        sourceCitations: ["artifact_1"],
        assumptions: ["Store managers can access the workflow on mobile."]
    }
};
const base = assessArtifactTrust({
    config: agentConfigs.bajie,
    context,
    artifact,
    schemaValid: true
});
const verifications = [
    {
        by: "houge",
        kind: "downstream_review",
        passed: true,
        reason: "猴哥 confirms the product brief is implementable."
    },
    {
        by: "shaseng",
        kind: "shaseng_eval",
        passed: true,
        reason: "沙僧 confirms the acceptance criteria can be tested."
    },
    {
        by: "tangseng",
        kind: "tangseng_decision",
        passed: true,
        reason: "唐僧 confirms this direction matches the approved MVP."
    }
];
const amplified = amplifyCollaborativeTrust({
    base,
    verifications
});
console.log(JSON.stringify({
    base,
    amplified,
    gate: trustGate(amplified)
}, null, 2));
