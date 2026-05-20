import { createJourney, transition } from "./journeyStateMachine.js";
import { MockStateSupervisor, superviseTransition } from "./stateSupervisor.js";
const supervisor = new MockStateSupervisor();
const events = [
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
        type: "bailongma.feedback.received",
        artifactIds: ["artifact_feedback_out_of_order"]
    }
];
let journey = createJourney("eng_001");
for (const event of events) {
    const result = transition(journey, event);
    const decision = await superviseTransition({
        current: journey,
        event,
        transition: result,
        supervisor
    });
    console.log(JSON.stringify({
        event: event.type,
        from: journey.state,
        to: result.next.state,
        commands: result.commands,
        supervisor: decision
    }, null, 2));
    journey = result.next;
}
