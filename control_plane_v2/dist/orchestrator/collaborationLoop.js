import { roleToolkits } from "../harness/toolCatalog.js";
export const collaborationLoop = [
    {
        stage: "founder_alignment",
        owner: "tangseng",
        inputFrom: "founder",
        outputTo: "bajie",
        purpose: "Confirm mission, scope, constraints, and the next iteration goal.",
        completionSignal: "tangseng.assignment.created"
    },
    {
        stage: "product_design",
        owner: "bajie",
        inputFrom: "tangseng",
        outputTo: "houge",
        purpose: "Shape the product idea, customer promise, Stitch prompt, and acceptance criteria.",
        completionSignal: "bajie.product_idea.created",
        downstreamReviewTarget: "tangseng"
    },
    {
        stage: "implementation",
        owner: "houge",
        inputFrom: "bajie",
        outputTo: "shaseng",
        purpose: "Build the approved product increment and record implementation evidence.",
        completionSignal: "houge.implementation.completed",
        downstreamReviewTarget: "bajie"
    },
    {
        stage: "quality_review",
        owner: "shaseng",
        inputFrom: "houge",
        outputTo: "bailongma",
        purpose: "Verify behavior, evaluate risks, and produce release evidence.",
        completionSignal: "shaseng.release_gate.passed",
        downstreamReviewTarget: "houge"
    },
    {
        stage: "customer_success",
        owner: "bailongma",
        inputFrom: "shaseng",
        outputTo: "tangseng",
        purpose: "Collect customer feedback, summarize value signals, and maintain the feedback cadence.",
        completionSignal: "bailongma.feedback.received",
        downstreamReviewTarget: "shaseng"
    },
    {
        stage: "planning_next_iteration",
        owner: "tangseng",
        inputFrom: "bailongma",
        outputTo: "founder",
        purpose: "Blend customer feedback, downstream reviews, and quality evidence into the next plan.",
        completionSignal: "tangseng.assignment.created",
        downstreamReviewTarget: "bailongma"
    }
];
export function buildIterationPlan(input) {
    return {
        iteration: input.iteration,
        goal: input.goal,
        nodes: collaborationLoop,
        learningSignals: collaborationLoop
            .filter((node) => Boolean(node.downstreamReviewTarget))
            .map((node) => ({
            reviewer: node.owner,
            reviewed: node.downstreamReviewTarget,
            timing: "after_reviewer_completes_own_step",
            affectsCurrentWorkflow: false,
            affectsFutureConfidence: true
        }))
    };
}
export function describeRoleToolkits() {
    return Object.entries(roleToolkits).map(([agentName, tools]) => ({
        agentName,
        tools: tools.map((tool) => ({
            name: tool.name,
            risk: tool.risk,
            requiresApproval: tool.requiresApproval,
            purpose: tool.purpose
        }))
    }));
}
