import type { AgentName } from "./types.js";
import type { TrustSignalKind } from "./trustHarness.js";

export type RoleHarnessSpec = {
  agentName: AgentName;
  mission: string;
  inputGate: string[];
  outputGate: string[];
  trustGate: {
    minimumInternalScore: number;
    minimumReleaseScore: number;
    requiredSignals: TrustSignalKind[];
  };
  crossChecks: Array<{
    reviewer: AgentName | "customer";
    checks: string[];
  }>;
  failureRouting: {
    reportTo: AgentName[];
    previousStep?: AgentName;
    recoveryPattern: string;
  };
};

export const roleHarnessSpecs: Record<AgentName, RoleHarnessSpec> = {
  tangseng: {
    agentName: "tangseng",
    mission: "Turn customer signals into a stable mission, scope, assignments, and adjustment decisions.",
    inputGate: [
      "Has customer transcript, feedback summary, or prior artifact.",
      "Separates facts, assumptions, open questions, and decisions.",
      "Identifies whether founder approval is required before team execution."
    ],
    outputGate: [
      "Produces mission, scope, non-goals, assignment list, and next state.",
      "Every assignment has owner, input artifacts, expected artifact, and stop condition.",
      "Any customer promise, pricing, or delivery date change is explicitly marked."
    ],
    trustGate: {
      minimumInternalScore: 0.78,
      minimumReleaseScore: 0.9,
      requiredSignals: ["schema_valid", "source_artifacts_present", "source_citations_present", "assumptions_declared"]
    },
    crossChecks: [
      {
        reviewer: "bajie",
        checks: ["Can this mission be explained clearly to customer stakeholders?"]
      },
      {
        reviewer: "houge",
        checks: ["Is the assignment technically actionable?"]
      },
      {
        reviewer: "shaseng",
        checks: ["Are acceptance criteria testable?"]
      },
      {
        reviewer: "bailongma",
        checks: ["Does this preserve customer value and adoption confidence?"]
      }
    ],
    failureRouting: {
      reportTo: ["tangseng"],
      recoveryPattern: "唐僧 revises the mission or asks the founder only when the mission cannot be safely resolved."
    }
  },

  bajie: {
    agentName: "bajie",
    mission: "Turn approved mission into product ideas, tradeoffs, and customer-readable communication.",
    inputGate: [
      "Has approved 唐僧 brief.",
      "Has target user and business outcome.",
      "Has known constraints and non-goals."
    ],
    outputGate: [
      "Provides 2-3 product options with tradeoffs.",
      "Marks recommended option and why.",
      "Defines what 猴哥 needs to implement.",
      "Provides customer-facing wording without overpromising."
    ],
    trustGate: {
      minimumInternalScore: 0.74,
      minimumReleaseScore: 0.88,
      requiredSignals: ["schema_valid", "source_artifacts_present", "source_citations_present", "assumptions_declared"]
    },
    crossChecks: [
      {
        reviewer: "houge",
        checks: ["Can this be implemented from the provided requirements?", "Are inputs and outputs explicit?"]
      },
      {
        reviewer: "shaseng",
        checks: ["Can acceptance criteria be evaluated?"]
      },
      {
        reviewer: "bailongma",
        checks: ["Will customers understand this?", "Does the message reduce adoption friction?"]
      }
    ],
    failureRouting: {
      reportTo: ["tangseng", "bajie"],
      previousStep: "tangseng",
      recoveryPattern: "唐僧 and 八戒 clarify product direction, then 八戒 reissues a tighter brief."
    }
  },

  houge: {
    agentName: "houge",
    mission: "Build the approved plan into working, testable implementation.",
    inputGate: [
      "Has 八戒 product brief or 唐僧 adjustment decision.",
      "Has explicit data inputs, outputs, and constraints.",
      "Has permission boundaries for repo, credentials, and deployment."
    ],
    outputGate: [
      "Produces technical plan, changed files, run instructions, and risk notes.",
      "Every implementation step is testable.",
      "Reports unclear requirements back to 八戒 and 唐僧 instead of guessing."
    ],
    trustGate: {
      minimumInternalScore: 0.78,
      minimumReleaseScore: 0.92,
      requiredSignals: ["schema_valid", "source_artifacts_present", "source_citations_present", "tool_result_attached"]
    },
    crossChecks: [
      {
        reviewer: "shaseng",
        checks: ["Do tests pass?", "Are edge cases covered?", "Are release risks acceptable?"]
      },
      {
        reviewer: "tangseng",
        checks: ["Does implementation stay inside scope?"]
      }
    ],
    failureRouting: {
      reportTo: ["tangseng", "bajie"],
      previousStep: "bajie",
      recoveryPattern: "猴哥 reports the ambiguity or implementation risk; 唐僧 and 八戒 adjust requirements before 猴哥 continues."
    }
  },

  shaseng: {
    agentName: "shaseng",
    mission: "Verify product, implementation, and agent behavior before release.",
    inputGate: [
      "Has implementation artifacts from 猴哥.",
      "Has acceptance criteria from 唐僧 or 八戒.",
      "Has eval dataset or explicit test cases."
    ],
    outputGate: [
      "Reports pass/fail with evidence.",
      "Separates must-fix issues from acceptable risks.",
      "Creates release gate decision and regression notes."
    ],
    trustGate: {
      minimumInternalScore: 0.8,
      minimumReleaseScore: 0.94,
      requiredSignals: ["schema_valid", "source_artifacts_present", "source_citations_present", "tool_result_attached", "shaseng_eval"]
    },
    crossChecks: [
      {
        reviewer: "houge",
        checks: ["Can failed cases be reproduced?", "Are fixes actionable?"]
      },
      {
        reviewer: "tangseng",
        checks: ["Should the release be held, adjusted, or accepted with known risk?"]
      }
    ],
    failureRouting: {
      reportTo: ["tangseng", "houge"],
      previousStep: "houge",
      recoveryPattern: "沙僧 routes failures to 猴哥 and 唐僧; 猴哥 fixes, 唐僧 decides whether scope or release posture changes."
    }
  },

  bailongma: {
    agentName: "bailongma",
    mission: "Keep customer feedback, adoption risk, and value delivery visible to 唐僧.",
    inputGate: [
      "Has delivered artifact, release candidate, or customer interaction.",
      "Has customer identity and relationship context.",
      "Knows whether message is routine or requires approval."
    ],
    outputGate: [
      "Summarizes sentiment, unresolved inputs, requested changes, and value signals.",
      "Drafts follow-up without overpromising.",
      "Routes important customer signals back to 唐僧."
    ],
    trustGate: {
      minimumInternalScore: 0.72,
      minimumReleaseScore: 0.88,
      requiredSignals: ["schema_valid", "source_artifacts_present", "source_citations_present", "assumptions_declared"]
    },
    crossChecks: [
      {
        reviewer: "tangseng",
        checks: ["Does this customer signal change scope, priority, or messaging?"]
      },
      {
        reviewer: "bajie",
        checks: ["Does the customer-facing wording land well?"]
      },
      {
        reviewer: "customer",
        checks: ["Does the customer confirm value or clarify unresolved input?"]
      }
    ],
    failureRouting: {
      reportTo: ["tangseng", "shaseng"],
      previousStep: "shaseng",
      recoveryPattern: "白龙马 reports adoption or value risk to 唐僧 and the previous step; 唐僧 decides whether product, release, or messaging changes."
    }
  }
};

export function getRoleHarnessSpec(agentName: AgentName) {
  return roleHarnessSpecs[agentName];
}
