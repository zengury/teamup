import type { AgentName } from "../harness/types.js";

export type JourneyState =
  | "idle"
  | "conversation_received"
  | "intake_ready"
  | "tangseng_planning"
  | "waiting_founder_approval"
  | "tangseng_adjusting"
  | "bajie_ideating"
  | "houge_building"
  | "shaseng_testing"
  | "bailongma_collecting_feedback"
  | "waiting_customer_feedback"
  | "release_ready"
  | "customer_delivered"
  | "retrospective_ready";

export type JourneyEvent =
  | { type: "conversation.transcribed"; artifactIds: string[] }
  | { type: "intake.completed"; artifactIds: string[] }
  | { type: "tangseng.brief.created"; artifactIds: string[]; approvalRequired: boolean }
  | { type: "tangseng.assignment.created"; artifactIds: string[]; approvalRequired: boolean }
  | { type: "tangseng.adjustment.decided"; target: AgentName; artifactIds: string[] }
  | { type: "founder.approved"; artifactIds: string[] }
  | { type: "founder.rejected"; reason: string }
  | { type: "bajie.product_idea.created"; artifactIds: string[] }
  | { type: "step.issue_reported"; owner: AgentName; reason: string; artifactIds: string[] }
  | { type: "houge.implementation.completed"; artifactIds: string[] }
  | { type: "shaseng.release_gate.passed"; artifactIds: string[] }
  | { type: "shaseng.release_gate.failed"; reason: string; artifactIds: string[] }
  | { type: "bailongma.feedback.received"; artifactIds: string[] }
  | { type: "bailongma.feedback_missing"; reason: string }
  | { type: "customer.approved"; artifactIds: string[] }
  | { type: "customer.revision_requested"; artifactIds: string[]; reason: string }
  | { type: "delivery.completed"; artifactIds: string[] }
  | { type: "retrospective.completed"; artifactIds: string[] }
  | { type: "iteration.next_planned"; artifactIds: string[]; approvalRequired: boolean };

export type JourneyCommand =
  | { type: "run_agent"; agentName: AgentName; triggerType: string; inputArtifactIds: string[] }
  | { type: "request_approval"; requestedFrom: "founder" | "customer"; reason: string; artifactIds: string[] }
  | { type: "route_issue"; owner: AgentName; previousAgent: AgentName; reason: string; artifactIds: string[] }
  | { type: "notify_founder"; message: string }
  | { type: "record_decision"; title: string; body: Record<string, unknown> };

export type JourneyContext = {
  engagementId: string;
  state: JourneyState;
  activeIssue?: {
    owner: AgentName;
    previousAgent: AgentName;
    reason: string;
    returnState: JourneyState;
  };
  lastArtifactIds: string[];
  history: Array<{
    state: JourneyState;
    eventType: JourneyEvent["type"];
  }>;
};

export type JourneyTransition = {
  next: JourneyContext;
  commands: JourneyCommand[];
};

export function createJourney(engagementId: string): JourneyContext {
  return {
    engagementId,
    state: "idle",
    lastArtifactIds: [],
    history: []
  };
}

export function transition(current: JourneyContext, event: JourneyEvent): JourneyTransition {
  const history = [...current.history, { state: current.state, eventType: event.type }];
  const base = {
    ...current,
    history
  };

  if (event.type === "step.issue_reported") {
    const previousAgent = previousAgentFor(event.owner);
    return {
      next: {
        ...base,
        state: "tangseng_adjusting",
        lastArtifactIds: event.artifactIds,
        activeIssue: {
          owner: event.owner,
          previousAgent,
          reason: event.reason,
          returnState: current.state
        }
      },
      commands: [
        {
          type: "route_issue",
          owner: event.owner,
          previousAgent,
          reason: event.reason,
          artifactIds: event.artifactIds
        },
        {
          type: "run_agent",
          agentName: "tangseng",
          triggerType: "step.issue_reported",
          inputArtifactIds: event.artifactIds
        },
        {
          type: "run_agent",
          agentName: previousAgent,
          triggerType: `${event.owner}.issue_reported`,
          inputArtifactIds: event.artifactIds
        }
      ]
    };
  }

  switch (current.state) {
    case "idle":
      return handleIdle(base, event);
    case "conversation_received":
      return handleConversationReceived(base, event);
    case "intake_ready":
      return handleIntakeReady(base, event);
    case "tangseng_planning":
      return handleTangsengPlanning(base, event);
    case "waiting_founder_approval":
      return handleFounderApproval(base, event);
    case "tangseng_adjusting":
      return handleTangsengAdjusting(base, event);
    case "bajie_ideating":
      return handleBajieIdeating(base, event);
    case "houge_building":
      return handleHougeBuilding(base, event);
    case "shaseng_testing":
      return handleShasengTesting(base, event);
    case "bailongma_collecting_feedback":
      return handleBailongmaFeedback(base, event);
    case "waiting_customer_feedback":
      return handleWaitingCustomerFeedback(base, event);
    case "release_ready":
      return handleReleaseReady(base, event);
    case "customer_delivered":
      return handleCustomerDelivered(base, event);
    case "retrospective_ready":
      return handleRetrospectiveReady(base, event);
  }
}

function handleIdle(current: JourneyContext, event: JourneyEvent): JourneyTransition {
  if (event.type !== "conversation.transcribed") return stay(current);
  return {
    next: withState(current, "conversation_received", event.artifactIds),
    commands: [
      {
        type: "run_agent",
        agentName: "tangseng",
        triggerType: "conversation.transcribed",
        inputArtifactIds: event.artifactIds
      }
    ]
  };
}

function handleConversationReceived(current: JourneyContext, event: JourneyEvent): JourneyTransition {
  if (event.type !== "intake.completed") return stay(current);
  return {
    next: withState(current, "intake_ready", event.artifactIds),
    commands: [
      {
        type: "run_agent",
        agentName: "tangseng",
        triggerType: "intake.completed",
        inputArtifactIds: event.artifactIds
      }
    ]
  };
}

function handleIntakeReady(current: JourneyContext, event: JourneyEvent): JourneyTransition {
  if (event.type !== "tangseng.brief.created") return stay(current);
  if (event.approvalRequired) {
    return {
      next: withState(current, "waiting_founder_approval", event.artifactIds),
      commands: [
        {
          type: "request_approval",
          requestedFrom: "founder",
          reason: "唐僧 brief needs founder approval before team execution.",
          artifactIds: event.artifactIds
        }
      ]
    };
  }

  return startExecutionAfterFounderApproval(current, event.artifactIds);
}

function handleTangsengPlanning(current: JourneyContext, event: JourneyEvent): JourneyTransition {
  if (event.type === "tangseng.brief.created") {
    return handleIntakeReady(current, event);
  }
  if (event.type === "tangseng.assignment.created") {
    if (event.approvalRequired) {
      return {
        next: withState(current, "waiting_founder_approval", event.artifactIds),
        commands: [
          {
            type: "request_approval",
            requestedFrom: "founder",
            reason: "唐僧 assignment needs founder approval before the team starts execution.",
            artifactIds: event.artifactIds
          }
        ]
      };
    }
    return startExecutionAfterFounderApproval(current, event.artifactIds);
  }
  if (event.type === "iteration.next_planned") {
    if (event.approvalRequired) {
      return {
        next: withState(current, "waiting_founder_approval", event.artifactIds),
        commands: [
          {
            type: "request_approval",
            requestedFrom: "founder",
            reason: "唐僧 next iteration plan needs founder approval before the team starts the next loop.",
            artifactIds: event.artifactIds
          }
        ]
      };
    }
    return startExecutionAfterFounderApproval(current, event.artifactIds);
  }
  if (event.type === "bailongma.feedback.received") {
    return {
      next: withState(current, "tangseng_planning", event.artifactIds),
      commands: [
        {
          type: "run_agent",
          agentName: "tangseng",
          triggerType: "bailongma.feedback.received",
          inputArtifactIds: event.artifactIds
        }
      ]
    };
  }
  return stay(current);
}

function handleFounderApproval(current: JourneyContext, event: JourneyEvent): JourneyTransition {
  if (event.type === "founder.rejected") {
    return {
      next: withState(current, "tangseng_planning", current.lastArtifactIds),
      commands: [
        {
          type: "run_agent",
          agentName: "tangseng",
          triggerType: "founder.rejected",
          inputArtifactIds: current.lastArtifactIds
        },
        {
          type: "record_decision",
          title: "Founder rejected brief",
          body: {
            reason: event.reason
          }
        }
      ]
    };
  }

  if (event.type !== "founder.approved") return stay(current);
  return startExecutionAfterFounderApproval(current, event.artifactIds);
}

function handleBajieIdeating(current: JourneyContext, event: JourneyEvent): JourneyTransition {
  if (event.type !== "bajie.product_idea.created") return stay(current);
  return {
    next: withState(current, "houge_building", event.artifactIds),
    commands: [
      {
        type: "run_agent",
        agentName: "houge",
        triggerType: "bajie.product_idea.created",
        inputArtifactIds: event.artifactIds
      }
    ]
  };
}

function handleTangsengAdjusting(current: JourneyContext, event: JourneyEvent): JourneyTransition {
  if (event.type !== "tangseng.adjustment.decided") return stay(current);
  return {
    next: withState(current, stateForAgent(event.target), event.artifactIds),
    commands: [
      {
        type: "run_agent",
        agentName: event.target,
        triggerType: "tangseng.adjustment.decided",
        inputArtifactIds: event.artifactIds
      },
      {
        type: "record_decision",
        title: "唐僧 adjustment decided",
        body: {
          target: event.target,
          priorIssue: current.activeIssue
        }
      }
    ]
  };
}

function handleHougeBuilding(current: JourneyContext, event: JourneyEvent): JourneyTransition {
  if (event.type !== "houge.implementation.completed") return stay(current);
  return {
    next: withState(current, "shaseng_testing", event.artifactIds),
    commands: [
      {
        type: "run_agent",
        agentName: "shaseng",
        triggerType: "houge.implementation.completed",
        inputArtifactIds: event.artifactIds
      }
    ]
  };
}

function handleShasengTesting(current: JourneyContext, event: JourneyEvent): JourneyTransition {
  if (event.type === "shaseng.release_gate.failed") {
    const previousAgent = previousAgentFor("shaseng");
    return {
      next: {
        ...withState(current, "tangseng_adjusting", event.artifactIds),
        activeIssue: {
          owner: "shaseng",
          previousAgent,
          reason: event.reason,
          returnState: "shaseng_testing"
        }
      },
      commands: [
        {
          type: "route_issue",
          owner: "shaseng",
          previousAgent,
          reason: event.reason,
          artifactIds: event.artifactIds
        },
        {
          type: "run_agent",
          agentName: "tangseng",
          triggerType: "shaseng.release_gate.failed",
          inputArtifactIds: event.artifactIds
        },
        {
          type: "run_agent",
          agentName: "houge",
          triggerType: "shaseng.release_gate.failed",
          inputArtifactIds: event.artifactIds
        },
        {
          type: "record_decision",
          title: "Release gate failed",
          body: {
            reason: event.reason
          }
        }
      ]
    };
  }

  if (event.type !== "shaseng.release_gate.passed") return stay(current);
  return {
    next: withState(current, "bailongma_collecting_feedback", event.artifactIds),
    commands: [
      {
        type: "run_agent",
        agentName: "bailongma",
        triggerType: "shaseng.release_gate.passed",
        inputArtifactIds: event.artifactIds
      }
    ]
  };
}

function handleBailongmaFeedback(current: JourneyContext, event: JourneyEvent): JourneyTransition {
  if (event.type === "bailongma.feedback_missing") {
    const previousAgent = previousAgentFor("bailongma");
    return {
      next: {
        ...withState(current, "tangseng_adjusting", current.lastArtifactIds),
        activeIssue: {
          owner: "bailongma",
          previousAgent,
          reason: event.reason,
          returnState: "bailongma_collecting_feedback"
        }
      },
      commands: [
        {
          type: "route_issue",
          owner: "bailongma",
          previousAgent,
          reason: event.reason,
          artifactIds: current.lastArtifactIds
        },
        {
          type: "run_agent",
          agentName: "tangseng",
          triggerType: "bailongma.feedback_missing",
          inputArtifactIds: current.lastArtifactIds
        },
        {
          type: "run_agent",
          agentName: previousAgent,
          triggerType: "bailongma.feedback_missing",
          inputArtifactIds: current.lastArtifactIds
        }
      ]
    };
  }

  if (event.type !== "bailongma.feedback.received") return stay(current);
  return {
    next: withState(current, "tangseng_planning", event.artifactIds),
    commands: [
      {
        type: "run_agent",
        agentName: "tangseng",
        triggerType: "bailongma.feedback.received",
        inputArtifactIds: event.artifactIds
      }
    ]
  };
}

function handleWaitingCustomerFeedback(current: JourneyContext, event: JourneyEvent): JourneyTransition {
  if (event.type === "bailongma.feedback.received") {
    return handleBailongmaFeedback(current, event);
  }
  if (event.type === "customer.approved") {
    return {
      next: withState(current, "release_ready", event.artifactIds),
      commands: [
        {
          type: "run_agent",
          agentName: "bailongma",
          triggerType: "customer.approved",
          inputArtifactIds: event.artifactIds
        }
      ]
    };
  }
  return stay(current);
}

function handleReleaseReady(current: JourneyContext, event: JourneyEvent): JourneyTransition {
  if (event.type === "customer.revision_requested") {
    return {
      next: withState(current, "tangseng_planning", event.artifactIds),
      commands: [
        {
          type: "run_agent",
          agentName: "tangseng",
          triggerType: "customer.revision_requested",
          inputArtifactIds: event.artifactIds
        },
        {
          type: "record_decision",
          title: "Customer requested revision",
          body: {
            reason: event.reason
          }
        }
      ]
    };
  }

  if (event.type !== "delivery.completed") return stay(current);
  return {
    next: withState(current, "customer_delivered", event.artifactIds),
    commands: [
      {
        type: "run_agent",
        agentName: "bailongma",
        triggerType: "delivery.completed",
        inputArtifactIds: event.artifactIds
      }
    ]
  };
}

function handleCustomerDelivered(current: JourneyContext, event: JourneyEvent): JourneyTransition {
  if (event.type !== "retrospective.completed") return stay(current);
  return {
    next: withState(current, "tangseng_planning", event.artifactIds),
    commands: [
      {
        type: "run_agent",
        agentName: "tangseng",
        triggerType: "retrospective.completed",
        inputArtifactIds: event.artifactIds
      },
      {
        type: "record_decision",
        title: "Journey retrospective completed",
        body: {
          artifactIds: event.artifactIds
        }
      }
    ]
  };
}

function handleRetrospectiveReady(current: JourneyContext, event: JourneyEvent): JourneyTransition {
  if (event.type !== "iteration.next_planned") return stay(current);
  if (event.approvalRequired) {
    return {
      next: withState(current, "waiting_founder_approval", event.artifactIds),
      commands: [
        {
          type: "request_approval",
          requestedFrom: "founder",
          reason: "唐僧 next iteration plan needs founder approval before the team starts the next loop.",
          artifactIds: event.artifactIds
        }
      ]
    };
  }

  return startExecutionAfterFounderApproval(current, event.artifactIds);
}

function startExecutionAfterFounderApproval(current: JourneyContext, artifactIds: string[]): JourneyTransition {
  return {
    next: withState(current, "bajie_ideating", artifactIds),
    commands: [
      {
        type: "run_agent",
        agentName: "bajie",
        triggerType: "founder.approved",
        inputArtifactIds: artifactIds
      }
    ]
  };
}

function withState(current: JourneyContext, state: JourneyState, artifactIds: string[]): JourneyContext {
  return {
    ...current,
    state,
    lastArtifactIds: artifactIds
  };
}

function stay(current: JourneyContext, commands: JourneyCommand[] = []): JourneyTransition {
  return {
    next: current,
    commands
  };
}

function previousAgentFor(owner: AgentName): AgentName {
  if (owner === "bajie") return "tangseng";
  if (owner === "houge") return "bajie";
  if (owner === "shaseng") return "houge";
  if (owner === "bailongma") return "shaseng";
  return "tangseng";
}

function stateForAgent(agentName: AgentName): JourneyState {
  if (agentName === "bajie") return "bajie_ideating";
  if (agentName === "houge") return "houge_building";
  if (agentName === "shaseng") return "shaseng_testing";
  if (agentName === "bailongma") return "bailongma_collecting_feedback";
  return "tangseng_planning";
}
