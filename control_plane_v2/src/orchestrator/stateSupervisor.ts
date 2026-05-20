import type { AgentEvent } from "../harness/types.js";
import type { JourneyContext, JourneyEvent, JourneyTransition } from "./journeyStateMachine.js";

export type SupervisorSeverity = "info" | "warning" | "critical";

export type SupervisorDecision =
  | {
      type: "accept";
      severity: "info";
      reason: string;
    }
  | {
      type: "ask_tangseng";
      severity: "warning";
      reason: string;
      suggestedEvent: AgentEvent;
    }
  | {
      type: "escalate_founder";
      severity: "critical";
      reason: string;
      suggestedQuestion: string;
    }
  | {
      type: "inject_event";
      severity: "warning";
      reason: string;
      event: JourneyEvent;
    };

export type SupervisorObservation = {
  current: JourneyContext;
  event: JourneyEvent;
  transition: JourneyTransition;
  findings: string[];
};

export type StateSupervisorAdapter = {
  review(observation: SupervisorObservation): Promise<SupervisorDecision>;
};

export async function superviseTransition(input: {
  current: JourneyContext;
  event: JourneyEvent;
  transition: JourneyTransition;
  supervisor: StateSupervisorAdapter;
}): Promise<SupervisorDecision> {
  const findings = deterministicFindings(input.current, input.event, input.transition);

  if (findings.some((finding) => finding.startsWith("critical:"))) {
    return {
      type: "escalate_founder",
      severity: "critical",
      reason: findings.join(" "),
      suggestedQuestion: "唐僧发现状态机进入不可恢复分支，需要你确认是否重置本次任务流。"
    };
  }

  if (findings.some((finding) => finding.startsWith("warning:"))) {
    return input.supervisor.review({
      current: input.current,
      event: input.event,
      transition: input.transition,
      findings
    });
  }

  return {
    type: "accept",
    severity: "info",
    reason: "State transition matches deterministic guardrails."
  };
}

function deterministicFindings(
  current: JourneyContext,
  event: JourneyEvent,
  transition: JourneyTransition
) {
  const findings: string[] = [];

  if (transition.next.state === current.state && transition.commands.length === 0) {
    findings.push(`warning: event ${event.type} produced no state change and no commands from ${current.state}.`);
  }

  if (transition.next.history.length > 20) {
    const recentStates = transition.next.history.slice(-8).map((entry) => entry.state);
    const uniqueRecentStates = new Set(recentStates);
    if (uniqueRecentStates.size <= 2) {
      findings.push("warning: possible state loop detected in recent history.");
    }
  }

  const founderApprovalCommands = transition.commands.filter(
    (command) => command.type === "request_approval" && command.requestedFrom === "founder"
  );
  if (founderApprovalCommands.length > 0 && current.state !== "intake_ready" && current.state !== "tangseng_planning") {
    findings.push("warning: founder approval requested outside the initial 唐僧 approval flow.");
  }

  const issueCommands = transition.commands.filter((command) => command.type === "route_issue");
  for (const command of issueCommands) {
    if (command.owner === command.previousAgent) {
      findings.push("critical: issue routing points to the same owner and previous agent.");
    }
    if (command.owner === "tangseng") {
      findings.push("warning: 唐僧 reported an issue; supervisor should decide whether founder escalation is needed.");
    }
  }

  return findings;
}

export class MockStateSupervisor implements StateSupervisorAdapter {
  async review(observation: SupervisorObservation): Promise<SupervisorDecision> {
    const noOp = observation.findings.find((finding) => finding.includes("no state change"));
    if (noOp) {
      return {
        type: "ask_tangseng",
        severity: "warning",
        reason: noOp,
        suggestedEvent: {
          type: "supervisor.review_requested",
          engagementId: observation.current.engagementId,
          payload: {
            state: observation.current.state,
            eventType: observation.event.type,
            reason: noOp
          }
        }
      };
    }

    return {
      type: "accept",
      severity: "info",
      reason: "Supervisor found no additional risk."
    };
  }
}
