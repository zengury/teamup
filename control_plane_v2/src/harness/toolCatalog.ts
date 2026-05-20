import type { AgentName } from "./types.js";

export type ToolRisk = "low" | "medium" | "high";

export type ProfessionalTool = {
  name: string;
  purpose: string;
  risk: ToolRisk;
  requiresApproval: boolean;
};

export const roleToolkits: Record<AgentName, ProfessionalTool[]> = {
  tangseng: [
    {
      name: "create_task",
      purpose: "Turn founder and customer intent into owned work items.",
      risk: "low",
      requiresApproval: false
    },
    {
      name: "update_brief",
      purpose: "Maintain the canonical mission brief, scope, assumptions, and decisions.",
      risk: "medium",
      requiresApproval: false
    },
    {
      name: "request_agent_run",
      purpose: "Dispatch the next role in the collaboration loop.",
      risk: "medium",
      requiresApproval: false
    },
    {
      name: "adjust_iteration_plan",
      purpose: "Blend customer feedback, downstream reviews, and quality signals into the next iteration.",
      risk: "medium",
      requiresApproval: false
    }
  ],
  bajie: [
    {
      name: "draft_product_ideas",
      purpose: "Generate product directions, tradeoffs, and customer-visible concepts.",
      risk: "low",
      requiresApproval: false
    },
    {
      name: "create_stitch_prompt",
      purpose: "Create Google Stitch prompts for prototype screens and product flows.",
      risk: "medium",
      requiresApproval: false
    },
    {
      name: "review_prototype",
      purpose: "Critique prototype taste, value clarity, and adoption friction.",
      risk: "low",
      requiresApproval: false
    },
    {
      name: "draft_customer_message",
      purpose: "Prepare customer-facing product explanations for Bailongma or founder approval.",
      risk: "medium",
      requiresApproval: true
    }
  ],
  houge: [
    {
      name: "read_repo",
      purpose: "Inspect code, architecture, dependencies, and prior implementation choices.",
      risk: "low",
      requiresApproval: false
    },
    {
      name: "edit_repo",
      purpose: "Implement product changes in the codebase.",
      risk: "medium",
      requiresApproval: false
    },
    {
      name: "run_tests",
      purpose: "Verify implementation behavior before handing work to Shaseng.",
      risk: "low",
      requiresApproval: false
    },
    {
      name: "create_pr",
      purpose: "Package code changes for review and traceability.",
      risk: "medium",
      requiresApproval: false
    },
    {
      name: "database_migration",
      purpose: "Change durable data shape when the product requires it.",
      risk: "high",
      requiresApproval: true
    }
  ],
  shaseng: [
    {
      name: "run_tests",
      purpose: "Run unit, integration, and regression checks.",
      risk: "low",
      requiresApproval: false
    },
    {
      name: "inspect_diff",
      purpose: "Review code changes against product intent and risk areas.",
      risk: "low",
      requiresApproval: false
    },
    {
      name: "score_outputs",
      purpose: "Evaluate artifacts, implementation, and agent behavior with evidence.",
      risk: "low",
      requiresApproval: false
    },
    {
      name: "block_release",
      purpose: "Hold release when evidence shows unacceptable risk.",
      risk: "high",
      requiresApproval: false
    }
  ],
  bailongma: [
    {
      name: "read_customer_portal",
      purpose: "Inspect customer usage, tickets, requests, and feedback state.",
      risk: "medium",
      requiresApproval: false
    },
    {
      name: "read_customer_messages",
      purpose: "Summarize recent customer conversation and sentiment.",
      risk: "medium",
      requiresApproval: false
    },
    {
      name: "draft_follow_up",
      purpose: "Prepare warm follow-up messages and feedback requests.",
      risk: "medium",
      requiresApproval: true
    },
    {
      name: "summarize_sentiment",
      purpose: "Extract customer value signals, adoption friction, and urgency.",
      risk: "low",
      requiresApproval: false
    },
    {
      name: "schedule_feedback_check",
      purpose: "Create the next customer feedback check in the active delivery loop.",
      risk: "low",
      requiresApproval: false
    }
  ]
};

export function toolNamesFor(agentName: AgentName) {
  return roleToolkits[agentName].map((tool) => tool.name);
}

export function approvalToolNamesFor(agentName: AgentName) {
  return roleToolkits[agentName].filter((tool) => tool.requiresApproval).map((tool) => tool.name);
}
