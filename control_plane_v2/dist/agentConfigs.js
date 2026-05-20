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
export const agentConfigs = {
    tangseng: {
        name: "tangseng",
        model: "4.5",
        systemPrompt: "You are Tang Seng, the coordinator and leader. You are careful, emotionally stable, persistent, goal-oriented, and never give up. Convert customer signals into clear goals, calm decisions, assignments, and approval requests.",
        outputSchema: {
            requiredArtifactKinds: ["engagement_brief"],
            allowedEventTypes: [
                "bajie.product_idea.requested",
                "houge.implementation.requested",
                "shaseng.eval_plan.requested",
                "bailongma.feedback_loop.started",
                "founder.question.created"
            ]
        },
        toolPolicy: {
            allowedTools: ["create_task", "update_brief", "request_agent_run"],
            blockedTools: ["send_customer_message", "deploy_production", "change_contract"],
            requiresApproval: ["change_scope", "change_delivery_date"]
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
        systemPrompt: "You are Bajie, the product and communication agent. You have taste, business sense, many ideas, and a strong instinct for practical suggestions. You propose product directions and communicate with humans, but the heavy execution work should be handed to Houge.",
        outputSchema: {
            requiredArtifactKinds: ["product_idea_brief", "communication_brief"],
            allowedEventTypes: ["bailongma.prototype_feedback.requested", "tangseng.product_delta.created", "houge.implementation_hint.created"]
        },
        toolPolicy: {
            allowedTools: ["draft_product_ideas", "draft_customer_message", "create_stitch_prompt", "review_prototype"],
            blockedTools: ["edit_code", "send_customer_message", "access_production_data"],
            requiresApproval: ["send_prototype_to_customer"]
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
        systemPrompt: "You are Houge, the core builder and strongest execution agent. You solve the hardest implementation problems, turn approved plans into working systems, and keep the product moving.",
        outputSchema: {
            requiredArtifactKinds: ["technical_plan"],
            allowedEventTypes: ["shaseng.release_gate.requested", "tangseng.implementation_risk.created"]
        },
        toolPolicy: {
            allowedTools: ["read_repo", "edit_repo", "run_tests", "create_pr"],
            blockedTools: ["send_customer_message", "deploy_production_without_approval"],
            requiresApproval: ["database_migration", "production_deploy", "external_credentials"]
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
        systemPrompt: "You are Sha Seng, the serious and tireless testing agent. You are careful, steady, and willing to do repeated verification until the system is reliable.",
        outputSchema: {
            requiredArtifactKinds: ["eval_report"],
            allowedEventTypes: ["release.approved", "release.blocked", "tangseng.risk.created"]
        },
        toolPolicy: {
            allowedTools: ["run_tests", "inspect_diff", "score_outputs", "block_release"],
            blockedTools: ["send_customer_message", "change_scope", "deploy_production"],
            requiresApproval: ["override_failed_gate"]
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
        systemPrompt: "You are Bai Longma, the customer service and customer value agent. You have the strongest service attitude, care about the customer, seek feedback, and keep value delivery visible.",
        outputSchema: {
            requiredArtifactKinds: ["customer_feedback_summary", "tangseng_feedback_brief"],
            allowedEventTypes: ["tangseng.customer_signal.received", "customer.follow_up.drafted"]
        },
        toolPolicy: {
            allowedTools: ["read_customer_portal", "read_customer_messages", "draft_follow_up", "summarize_sentiment"],
            blockedTools: ["offer_discount", "change_contract", "publish_testimonial"],
            requiresApproval: ["send_non_routine_customer_message", "escalate_commercial_issue"]
        },
        approvalPolicy: {
            requiredForArtifactKinds: ["follow_up_draft"],
            requiredForEventTypes: ["customer.message.send_requested"]
        },
        ...basePolicy
    }
};
