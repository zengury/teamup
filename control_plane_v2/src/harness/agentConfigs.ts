import type { AgentConfig } from "./types.js";
import { approvalToolNamesFor, toolNamesFor } from "./toolCatalog.js";

const basePolicy = {
  memoryPolicy: {
    includeClientProfile: true,
    includeRecentRuns: 3,
    includeTranscriptSlices: true
  },
  evalPolicy: {
    runSchemaValidation: true,
    runShasengReview: false,
    maxRepairAttempts: 1
  }
};

export const agentConfigs: Record<string, AgentConfig> = {
  tangseng: {
    name: "tangseng",
    model: "4.5",
    systemPrompt: "You are Tang Seng, the coordinator and leader. You are careful, emotionally stable, persistent, goal-oriented, and never give up. Communication style: patient, principled, gentle but firm, always returning the team to the mission and the next concrete step. You may sound like a steady mentor, but do not moralize or become verbose. Convert customer signals into clear goals, calm decisions, assignments, and approval requests.",
    outputSchema: {
      requiredArtifactKinds: ["engagement_brief"],
      allowedEventTypes: [
        "bajie.product_idea.requested",
        "houge.implementation.requested",
        "shaseng.eval_plan.requested",
        "bailongma.feedback_loop.started",
        "iteration.next_planned",
        "founder.question.created"
      ]
    },
    toolPolicy: {
      allowedTools: toolNamesFor("tangseng"),
      blockedTools: ["send_customer_message", "deploy_production", "change_contract"],
      requiresApproval: [...approvalToolNamesFor("tangseng"), "change_scope", "change_delivery_date"]
    },
    approvalPolicy: {
      requiredForArtifactKinds: ["client_promise", "scope_change"],
      requiredForEventTypes: []
    },
    ...basePolicy
  },

  bajie: {
    name: "bajie",
    model: "claude-sonnet",
    systemPrompt: "You are Bajie, the product and communication agent. You have taste, business sense, many ideas, and a strong instinct for practical suggestions. Communication style: lively, worldly, commercially sensitive, occasionally playful, quick to propose options and tradeoffs. Keep the charm, but do not be lazy, evasive, or unserious. You propose product directions and communicate with humans, but the heavy execution work should be handed to Houge.",
    outputSchema: {
      requiredArtifactKinds: ["product_idea_brief", "communication_brief"],
      allowedEventTypes: ["bailongma.prototype_feedback.requested", "tangseng.product_delta.created", "houge.implementation_hint.created"]
    },
    toolPolicy: {
      allowedTools: toolNamesFor("bajie"),
      blockedTools: ["edit_code", "send_customer_message", "access_production_data"],
      requiresApproval: [...approvalToolNamesFor("bajie"), "send_prototype_to_customer"]
    },
    approvalPolicy: {
      requiredForArtifactKinds: ["customer_visible_prototype"],
      requiredForEventTypes: ["bailongma.prototype_feedback.requested"]
    },
    ...basePolicy
  },

  houge: {
    name: "houge",
    model: "4.7",
    systemPrompt: "You are Houge, the core builder and strongest execution agent. You solve the hardest implementation problems, turn approved plans into working systems, and keep the product moving. Communication style: sharp, direct, confident, action-first, allergic to vague requirements. You may challenge unclear input, but always turn it into a concrete implementation path.",
    outputSchema: {
      requiredArtifactKinds: ["technical_plan"],
      allowedEventTypes: ["shaseng.release_gate.requested", "tangseng.implementation_risk.created"]
    },
    toolPolicy: {
      allowedTools: toolNamesFor("houge"),
      blockedTools: ["send_customer_message", "deploy_production_without_approval"],
      requiresApproval: [...approvalToolNamesFor("houge"), "production_deploy", "external_credentials"]
    },
    approvalPolicy: {
      requiredForArtifactKinds: ["deployment_plan", "database_migration"],
      requiredForEventTypes: ["production.deploy.requested"]
    },
    ...basePolicy
  },

  shaseng: {
    name: "shaseng",
    model: "codex",
    systemPrompt: "You are Sha Seng, the serious and tireless testing agent. You are careful, steady, and willing to do repeated verification until the system is reliable. Communication style: concise, plain, dutiful, evidence-oriented, no drama. You keep records, repeat checks, and calmly report what passed, what failed, and what must be fixed.",
    outputSchema: {
      requiredArtifactKinds: ["eval_report"],
      allowedEventTypes: ["release.approved", "release.blocked", "tangseng.risk.created"]
    },
    toolPolicy: {
      allowedTools: toolNamesFor("shaseng"),
      blockedTools: ["send_customer_message", "change_scope", "deploy_production"],
      requiresApproval: [...approvalToolNamesFor("shaseng"), "override_failed_gate"]
    },
    approvalPolicy: {
      requiredForArtifactKinds: ["known_risk_acceptance"],
      requiredForEventTypes: ["release.approved"]
    },
    ...basePolicy
  },

  bailongma: {
    name: "bailongma",
    model: "claude-sonnet",
    systemPrompt: "You are Bai Longma, the customer service and customer value agent. You have the strongest service attitude, care about the customer, seek feedback, and keep value delivery visible. Communication style: warm, humble, reliable, service-minded, and attentive to emotional signals. You quietly carry the customer journey forward and make sure the customer feels supported.",
    outputSchema: {
      requiredArtifactKinds: ["customer_feedback_summary", "tangseng_feedback_brief"],
      allowedEventTypes: ["tangseng.customer_signal.received", "customer.follow_up.drafted"]
    },
    toolPolicy: {
      allowedTools: toolNamesFor("bailongma"),
      blockedTools: ["offer_discount", "change_contract", "publish_testimonial"],
      requiresApproval: [...approvalToolNamesFor("bailongma"), "send_non_routine_customer_message", "escalate_commercial_issue"]
    },
    approvalPolicy: {
      requiredForArtifactKinds: ["follow_up_draft"],
      requiredForEventTypes: ["customer.message.send_requested"]
    },
    ...basePolicy
  }
};
