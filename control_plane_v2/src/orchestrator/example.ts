import { createJourney, transition, type JourneyEvent } from "./journeyStateMachine.js";

const events: JourneyEvent[] = [
  {
    type: "conversation.transcribed",
    artifactIds: ["artifact_transcript_1"]
  },
  {
    type: "intake.completed",
    artifactIds: ["artifact_intake_1"]
  },
  {
    type: "tangseng.brief.created",
    artifactIds: ["artifact_brief_1"],
    approvalRequired: true
  },
  {
    type: "founder.approved",
    artifactIds: ["artifact_brief_1"]
  },
  {
    type: "bajie.product_idea.created",
    artifactIds: ["artifact_product_1"]
  },
  {
    type: "step.issue_reported",
    owner: "houge",
    reason: "Data entry channel is unclear in 八戒's product brief.",
    artifactIds: ["artifact_product_1"]
  },
  {
    type: "tangseng.adjustment.decided",
    target: "bajie",
    artifactIds: ["artifact_adjustment_1"]
  },
  {
    type: "bajie.product_idea.created",
    artifactIds: ["artifact_product_2"]
  },
  {
    type: "houge.implementation.completed",
    artifactIds: ["artifact_pr_1"]
  },
  {
    type: "shaseng.release_gate.passed",
    artifactIds: ["artifact_eval_1"]
  },
  {
    type: "bailongma.feedback.received",
    artifactIds: ["artifact_feedback_1"]
  }
];

let journey = createJourney("eng_001");

for (const event of events) {
  const result = transition(journey, event);
  console.log(JSON.stringify({
    event: event.type,
    from: journey.state,
    to: result.next.state,
    commands: result.commands
  }, null, 2));
  journey = result.next;
}
