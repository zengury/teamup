export function collectCustomerFeedback(input) {
    const sourceCounts = countSources(input.sources);
    const signals = input.sources.flatMap(signalFromSource);
    const silenceSignal = input.customerRespondedWithinSla
        ? []
        : [
            {
                sourceId: "sla",
                kind: "customer_message",
                signalType: "silence",
                sentiment: "unknown",
                summary: "Customer has not responded within the expected feedback window.",
                urgency: "medium"
            }
        ];
    const allSignals = [...signals, ...silenceSignal];
    const shouldDraftFollowUp = !input.customerRespondedWithinSla || input.openQuestions.length > 0;
    return {
        engagementId: input.engagementId,
        sourcesChecked: sourceCounts,
        signals: allSignals,
        unansweredQuestions: input.openQuestions,
        shouldDraftFollowUp,
        followUpReason: shouldDraftFollowUp ? followUpReason(input) : undefined,
        tangsengBrief: {
            sentiment: aggregateSentiment(allSignals),
            recommendedNextAction: recommendedNextAction(allSignals, input.openQuestions),
            evidenceSourceIds: input.sources.map((source) => source.id)
        }
    };
}
function countSources(sources) {
    const counts = new Map();
    for (const source of sources) {
        counts.set(source.kind, (counts.get(source.kind) ?? 0) + 1);
    }
    return Array.from(counts.entries()).map(([kind, count]) => ({ kind, count }));
}
function signalFromSource(source) {
    const text = source.text?.toLowerCase() ?? "";
    const signals = [];
    if (text.includes("useful") || text.includes("helpful") || text.includes("works")) {
        signals.push({
            sourceId: source.id,
            kind: source.kind,
            signalType: "value_signal",
            sentiment: "positive",
            summary: `${source.title}: customer described the current delivery as useful.`,
            urgency: "low"
        });
    }
    if (text.includes("confusing") || text.includes("too much") || text.includes("hard")) {
        signals.push({
            sourceId: source.id,
            kind: source.kind,
            signalType: "adoption_friction",
            sentiment: "negative",
            summary: `${source.title}: customer showed adoption friction or confusion.`,
            urgency: "medium"
        });
    }
    if (text.includes("can it") || text.includes("could it") || text.includes("want")) {
        signals.push({
            sourceId: source.id,
            kind: source.kind,
            signalType: "feature_request",
            sentiment: "neutral-positive",
            summary: `${source.title}: customer hinted at a feature request or expansion path.`,
            urgency: "medium"
        });
    }
    if (source.kind === "usage_metric" && source.metrics) {
        signals.push({
            sourceId: source.id,
            kind: source.kind,
            signalType: "usage_signal",
            sentiment: source.metrics.activeUsers && source.metrics.activeUsers > 0 ? "neutral-positive" : "unknown",
            summary: `${source.title}: usage metrics were captured for adoption review.`,
            urgency: "low"
        });
    }
    return signals;
}
function aggregateSentiment(signals) {
    if (signals.some((signal) => signal.sentiment === "negative"))
        return "negative";
    if (signals.some((signal) => signal.sentiment === "positive"))
        return "positive";
    if (signals.some((signal) => signal.sentiment === "neutral-positive"))
        return "neutral-positive";
    if (signals.some((signal) => signal.sentiment === "neutral"))
        return "neutral";
    return "unknown";
}
function recommendedNextAction(signals, openQuestions) {
    if (signals.some((signal) => signal.signalType === "adoption_friction")) {
        return "Ask 八戒 to simplify the product path and ask 猴哥 to prioritize the friction point.";
    }
    if (openQuestions.length > 0) {
        return "Ask 白龙马 to draft a focused follow-up for the unresolved questions.";
    }
    if (signals.some((signal) => signal.signalType === "feature_request")) {
        return "Ask 唐僧 to decide whether the request belongs in the next iteration or future backlog.";
    }
    return "Continue the feedback cadence and keep the current iteration direction.";
}
function followUpReason(input) {
    if (!input.customerRespondedWithinSla)
        return "Customer has not responded within SLA.";
    return `There are unresolved customer questions: ${input.openQuestions.join("; ")}`;
}
