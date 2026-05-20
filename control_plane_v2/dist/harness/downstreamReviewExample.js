import { agentConfigs } from "./agentConfigs.js";
import { applyDownstreamReview, assessArtifactTrust, downstreamLearningSignal, upstreamConfidenceAdjustment } from "./trustHarness.js";
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
const bajieArtifact = {
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
    artifact: bajieArtifact,
    schemaValid: true
});
const hougeReview = {
    upstreamAgent: "bajie",
    downstreamAgent: "houge",
    targetArtifactId: "artifact_product_idea_1",
    downstreamArtifactId: "artifact_houge_implementation_1",
    learnedAfterCompletion: true,
    dimensions: [
        {
            name: "implementability",
            score: 0.78,
            reason: "Core workflow is implementable."
        },
        {
            name: "input_output_clarity",
            score: 0.58,
            reason: "Data entry channel and payload shape are not explicit enough."
        },
        {
            name: "scope_control",
            score: 0.74,
            reason: "MVP boundary is mostly clear."
        }
    ],
    futureAdjustmentHints: [
        "In future product briefs, specify the first data entry channel and required payload fields before implementation starts."
    ]
};
const amplified = applyDownstreamReview({
    base,
    review: hougeReview
});
console.log(JSON.stringify({
    base,
    downstreamReview: hougeReview,
    downstreamLearningSignal: downstreamLearningSignal(hougeReview),
    upstreamConfidenceAdjustment: upstreamConfidenceAdjustment({
        priorConfidence: 0.84,
        review: hougeReview,
        downstreamReviewWeight: 0.2
    }),
    amplified
}, null, 2));
