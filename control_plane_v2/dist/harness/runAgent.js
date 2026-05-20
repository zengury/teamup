import { assessArtifactTrust, attachTrustToArtifactBody } from "./trustHarness.js";
export async function runAgent(config, request, deps) {
    assertRequestMatchesConfig(config, request);
    const run = await deps.store.createRun({
        engagementId: request.engagementId,
        agentName: config.name,
        triggerType: request.triggerType,
        model: config.model
    });
    try {
        await deps.store.updateRun(run.id, {
            runId: run.id,
            status: "building_context",
            outputArtifactIds: [],
            nextEvents: []
        });
        const context = await buildContext(config, request, deps.store);
        await deps.store.updateRun(run.id, {
            runId: run.id,
            status: "running",
            outputArtifactIds: [],
            nextEvents: []
        });
        const output = await deps.model.complete({
            model: config.model,
            systemPrompt: config.systemPrompt,
            context,
            triggerPayload: request.triggerPayload
        });
        const validation = validateOutput(config, output);
        if (!validation.ok) {
            const failed = {
                runId: run.id,
                status: "failed",
                outputArtifactIds: [],
                nextEvents: [],
                error: validation.error
            };
            await deps.store.updateRun(run.id, failed);
            return failed;
        }
        const savedArtifacts = await storeArtifacts(config, request, context, output, deps.store);
        const events = output.events.map((event) => ({
            type: event.type,
            engagementId: request.engagementId,
            payload: event.payload
        }));
        const approvalRequest = buildApprovalRequest(config, output, savedArtifacts, events);
        if (approvalRequest) {
            await deps.store.saveApproval(run.id, approvalRequest);
            const waiting = {
                runId: run.id,
                status: "waiting_for_approval",
                outputArtifactIds: savedArtifacts.map((artifact) => artifact.id),
                nextEvents: events,
                approvalRequest
            };
            await deps.store.updateRun(run.id, waiting);
            return waiting;
        }
        await Promise.all(events.map((event) => deps.store.emitEvent(event)));
        const completed = {
            runId: run.id,
            status: "completed",
            outputArtifactIds: savedArtifacts.map((artifact) => artifact.id),
            nextEvents: events
        };
        await deps.store.updateRun(run.id, completed);
        return completed;
    }
    catch (error) {
        const failed = {
            runId: run.id,
            status: "failed",
            outputArtifactIds: [],
            nextEvents: [],
            error: error instanceof Error ? error.message : "Unknown harness error"
        };
        await deps.store.updateRun(run.id, failed);
        return failed;
    }
}
function assertRequestMatchesConfig(config, request) {
    if (config.name !== request.agentName) {
        throw new Error(`Config agent ${config.name} cannot run request for ${request.agentName}`);
    }
}
async function buildContext(config, request, store) {
    const sourceArtifacts = await store.getArtifacts(request.inputArtifactIds);
    return {
        engagementId: request.engagementId,
        agentName: config.name,
        triggerType: request.triggerType,
        facts: extractFacts(sourceArtifacts),
        sourceArtifacts,
        workingNotes: [
            `Model route: ${config.model}`,
            `Allowed tools: ${config.toolPolicy.allowedTools.join(", ")}`,
            `Blocked tools: ${config.toolPolicy.blockedTools.join(", ")}`
        ]
    };
}
function extractFacts(artifacts) {
    return artifacts.map((artifact) => `${artifact.kind}: ${artifact.title}`);
}
function validateOutput(config, output) {
    if (!Array.isArray(output.artifacts)) {
        return { ok: false, error: "Agent output must include artifacts array" };
    }
    if (!Array.isArray(output.events)) {
        return { ok: false, error: "Agent output must include events array" };
    }
    const artifactKinds = new Set(output.artifacts.map((artifact) => artifact.kind));
    const missingKind = config.outputSchema.requiredArtifactKinds.find((kind) => !artifactKinds.has(kind));
    if (missingKind) {
        return { ok: false, error: `Missing required artifact kind: ${missingKind}` };
    }
    const disallowedEvent = output.events.find((event) => !config.outputSchema.allowedEventTypes.includes(event.type));
    if (disallowedEvent) {
        return { ok: false, error: `Disallowed event type for ${config.name}: ${disallowedEvent.type}` };
    }
    return { ok: true };
}
async function storeArtifacts(config, request, context, output, store) {
    const artifacts = [];
    for (const artifact of output.artifacts) {
        const bodyWithSourceContext = {
            ...artifact.body,
            sourceContext: {
                triggerType: context.triggerType,
                sourceArtifactIds: request.inputArtifactIds
            }
        };
        artifacts.push(await store.saveArtifact({
            engagementId: request.engagementId,
            kind: artifact.kind,
            title: artifact.title,
            body: attachTrustToArtifactBody(bodyWithSourceContext, assessArtifactTrust({
                config,
                context,
                artifact: {
                    ...artifact,
                    body: bodyWithSourceContext
                },
                schemaValid: true
            })),
            status: artifact.status ?? "draft",
            createdByAgent: config.name,
            sourceArtifactIds: request.inputArtifactIds
        }));
    }
    return artifacts;
}
function buildApprovalRequest(config, output, artifacts, events) {
    const artifactNeedsApproval = artifacts.some((artifact) => config.approvalPolicy.requiredForArtifactKinds.includes(artifact.kind));
    const eventNeedsApproval = events.some((event) => config.approvalPolicy.requiredForEventTypes.includes(event.type));
    if (!artifactNeedsApproval && !eventNeedsApproval && !output.approvalRequest) {
        return undefined;
    }
    return {
        type: output.approvalRequest?.type ?? "agent_output_approval",
        requestedFrom: output.approvalRequest?.requestedFrom ?? "founder",
        reason: output.approvalRequest?.reason ?? `Approval required by ${config.name} harness policy`,
        artifactIds: artifacts.map((artifact) => artifact.id)
    };
}
