import type { AgentConfig, AgentName, Artifact, ContextPacket } from "./types.js";
import { getRoleHarnessSpec } from "./roleHarnessSpecs.js";

export type TrustLevel = "untrusted" | "provisional" | "trusted" | "release_ready";

export type TrustSignalKind =
  | "schema_valid"
  | "source_artifacts_present"
  | "source_citations_present"
  | "assumptions_declared"
  | "tool_result_attached"
  | "upstream_review"
  | "downstream_review"
  | "shaseng_eval"
  | "tangseng_decision"
  | "customer_confirmation";

export type TrustSignal = {
  kind: TrustSignalKind;
  source: AgentName | "system" | "customer";
  passed: boolean;
  weight: number;
  reason: string;
};

export type TrustAssessment = {
  score: number;
  level: TrustLevel;
  signals: TrustSignal[];
  requiredActions: string[];
};

export type Verification = {
  by: AgentName | "customer";
  kind: TrustSignalKind;
  passed: boolean;
  reason: string;
};

export type DownstreamReview = {
  upstreamAgent: AgentName;
  downstreamAgent: AgentName;
  targetArtifactId?: string;
  downstreamArtifactId?: string;
  dimensions: Array<{
    name: string;
    score: number;
    reason: string;
  }>;
  learnedAfterCompletion: boolean;
  futureAdjustmentHints: string[];
};

export type ArtifactDraft = {
  kind: string;
  title: string;
  body: Record<string, unknown>;
};

export function assessArtifactTrust(input: {
  config: AgentConfig;
  context: ContextPacket;
  artifact: ArtifactDraft;
  schemaValid: boolean;
}): TrustAssessment {
  const signals: TrustSignal[] = [
    {
      kind: "schema_valid",
      source: "system",
      passed: input.schemaValid,
      weight: 0.25,
      reason: input.schemaValid ? "Artifact matched the agent output schema." : "Artifact failed schema validation."
    },
    {
      kind: "source_artifacts_present",
      source: "system",
      passed: input.context.sourceArtifacts.length > 0,
      weight: 0.18,
      reason:
        input.context.sourceArtifacts.length > 0
          ? "Artifact was generated from durable source artifacts."
          : "Artifact has no durable source artifacts."
    },
    {
      kind: "source_citations_present",
      source: "system",
      passed: hasSourceCitations(input.artifact.body),
      weight: 0.17,
      reason: hasSourceCitations(input.artifact.body)
        ? "Artifact includes source citations or source context."
        : "Artifact lacks explicit source citations."
    },
    {
      kind: "assumptions_declared",
      source: input.config.name,
      passed: hasDeclaredAssumptions(input.artifact.body),
      weight: 0.12,
      reason: hasDeclaredAssumptions(input.artifact.body)
        ? "Agent declared assumptions or uncertainty."
        : "Agent did not declare assumptions."
    },
    {
      kind: "tool_result_attached",
      source: "system",
      passed: hasToolResult(input.artifact.body),
      weight: 0.13,
      reason: hasToolResult(input.artifact.body)
        ? "Artifact contains tool-backed evidence."
        : "No tool-backed evidence was attached."
    }
  ];

  return scoreTrust(signals);
}

export function amplifyCollaborativeTrust(input: {
  base: TrustAssessment;
  verifications: Verification[];
}): TrustAssessment {
  const signals = [
    ...input.base.signals,
    ...input.verifications.map((verification) => ({
      kind: verification.kind,
      source: verification.by,
      passed: verification.passed,
      weight: weightForVerification(verification.kind),
      reason: verification.reason
    }))
  ];

  return scoreTrust(signals);
}

export function downstreamReviewToVerification(review: DownstreamReview): Verification {
  const average = averageDimensionScore(review);
  return {
    by: review.downstreamAgent,
    kind: "downstream_review",
    passed: review.learnedAfterCompletion && average >= 0.72,
    reason: [
      `${review.downstreamAgent} reviewed ${review.upstreamAgent} output after completing its own step.`,
      `Retrospective upstream quality score: ${average.toFixed(2)}.`,
      review.downstreamArtifactId ? `Downstream completion artifact: ${review.downstreamArtifactId}.` : "",
      ...review.dimensions.map((dimension) => `${dimension.name}: ${dimension.score.toFixed(2)} - ${dimension.reason}`),
      ...review.futureAdjustmentHints.map((hint) => `Future adjustment hint: ${hint}`)
    ]
      .filter(Boolean)
      .join(" ")
  };
}

export function applyDownstreamReview(input: {
  base: TrustAssessment;
  review: DownstreamReview;
}): TrustAssessment {
  return amplifyCollaborativeTrust({
    base: input.base,
    verifications: [downstreamReviewToVerification(input.review)]
  });
}

export function downstreamLearningSignal(review: DownstreamReview): {
  affectsCurrentWorkflow: false;
  averageScore: number;
  upstreamAgent: AgentName;
  downstreamAgent: AgentName;
  futureAdjustmentHints: string[];
  reason: string;
} {
  const averageScore = averageDimensionScore(review);

  return {
    affectsCurrentWorkflow: false,
    averageScore,
    upstreamAgent: review.upstreamAgent,
    downstreamAgent: review.downstreamAgent,
    futureAdjustmentHints: review.futureAdjustmentHints,
    reason: `${review.downstreamAgent} scores ${review.upstreamAgent} after completing its own step; this updates future upstream confidence and does not block the current workflow.`
  };
}

export function upstreamConfidenceAdjustment(input: {
  priorConfidence: number;
  review: DownstreamReview;
  downstreamReviewWeight?: number;
}): {
  upstreamAgent: AgentName;
  priorConfidence: number;
  downstreamReviewScore: number;
  downstreamReviewWeight: number;
  updatedFutureConfidence: number;
  reason: string;
} {
  const downstreamReviewWeight = input.downstreamReviewWeight ?? 0.2;
  const priorWeight = 1 - downstreamReviewWeight;
  const priorConfidence = clamp01(input.priorConfidence);
  const downstreamReviewScore = averageDimensionScore(input.review);
  const updatedFutureConfidence = round(priorConfidence * priorWeight + downstreamReviewScore * downstreamReviewWeight);

  return {
    upstreamAgent: input.review.upstreamAgent,
    priorConfidence,
    downstreamReviewScore,
    downstreamReviewWeight,
    updatedFutureConfidence,
    reason: `${input.review.downstreamAgent}'s post-completion review updates ${input.review.upstreamAgent}'s future confidence from ${priorConfidence.toFixed(2)} to ${updatedFutureConfidence.toFixed(2)}.`
  };
}

export function trustGate(assessment: TrustAssessment): {
  allowed: boolean;
  reason: string;
  requiredActions: string[];
} {
  if (assessment.score >= 0.72) {
    return {
      allowed: true,
      reason: `Trust score ${assessment.score.toFixed(2)} is sufficient for the next internal step.`,
      requiredActions: []
    };
  }

  return {
    allowed: false,
    reason: `Trust score ${assessment.score.toFixed(2)} is below the internal handoff threshold.`,
    requiredActions: assessment.requiredActions
  };
}

export function roleTrustGate(input: {
  agentName: AgentName;
  assessment: TrustAssessment;
  releaseSensitive?: boolean;
}): {
  allowed: boolean;
  reason: string;
  requiredActions: string[];
} {
  const spec = getRoleHarnessSpec(input.agentName);
  const minimum = input.releaseSensitive ? spec.trustGate.minimumReleaseScore : spec.trustGate.minimumInternalScore;
  const missingRequiredSignals = spec.trustGate.requiredSignals.filter((kind) =>
    input.assessment.signals.every((signal) => signal.kind !== kind || !signal.passed)
  );

  if (missingRequiredSignals.length > 0) {
    return {
      allowed: false,
      reason: `${input.agentName} output is missing required trust signals: ${missingRequiredSignals.join(", ")}.`,
      requiredActions: missingRequiredSignals.map(actionForMissingSignal)
    };
  }

  if (input.assessment.score < minimum) {
    return {
      allowed: false,
      reason: `${input.agentName} trust score ${input.assessment.score.toFixed(2)} is below required ${minimum.toFixed(2)}.`,
      requiredActions: input.assessment.requiredActions
    };
  }

  return {
    allowed: true,
    reason: `${input.agentName} trust score ${input.assessment.score.toFixed(2)} passes role harness threshold ${minimum.toFixed(2)}.`,
    requiredActions: []
  };
}

export function attachTrustToArtifactBody(body: Record<string, unknown>, trust: TrustAssessment) {
  return {
    ...body,
    trust: {
      score: trust.score,
      level: trust.level,
      requiredActions: trust.requiredActions,
      signals: trust.signals.map((signal) => ({
        kind: signal.kind,
        source: signal.source,
        passed: signal.passed,
        reason: signal.reason
      }))
    }
  };
}

function scoreTrust(signals: TrustSignal[]): TrustAssessment {
  const totalWeight = signals.reduce((total, signal) => total + signal.weight, 0);
  const passedWeight = signals.reduce((total, signal) => total + (signal.passed ? signal.weight : 0), 0);
  const score = totalWeight === 0 ? 0 : round(passedWeight / totalWeight);
  const requiredActions = signals
    .filter((signal) => !signal.passed)
    .map((signal) => actionForMissingSignal(signal.kind));

  return {
    score,
    level: levelForScore(score),
    signals,
    requiredActions: [...new Set(requiredActions)]
  };
}

function levelForScore(score: number): TrustLevel {
  if (score >= 0.9) return "release_ready";
  if (score >= 0.72) return "trusted";
  if (score >= 0.45) return "provisional";
  return "untrusted";
}

function hasSourceCitations(body: Record<string, unknown>) {
  return Boolean(body.sourceContext) || Array.isArray(body.sourceCitations);
}

function hasDeclaredAssumptions(body: Record<string, unknown>) {
  return Array.isArray(body.assumptions) || Array.isArray(body.uncertainties);
}

function hasToolResult(body: Record<string, unknown>) {
  return Array.isArray(body.toolResults) || Boolean(body.toolResult);
}

function weightForVerification(kind: TrustSignalKind) {
  if (kind === "customer_confirmation") return 0.28;
  if (kind === "shaseng_eval") return 0.24;
  if (kind === "tangseng_decision") return 0.2;
  if (kind === "downstream_review") return 0.18;
  if (kind === "upstream_review") return 0.16;
  return 0.1;
}

function actionForMissingSignal(kind: TrustSignalKind) {
  if (kind === "source_citations_present") return "Add source citations or sourceContext.";
  if (kind === "source_artifacts_present") return "Attach durable source artifacts.";
  if (kind === "assumptions_declared") return "Declare assumptions and uncertainties.";
  if (kind === "tool_result_attached") return "Attach tool-backed evidence where possible.";
  if (kind === "schema_valid") return "Repair artifact schema.";
  if (kind === "downstream_review") return "Record downstream learning signal and adjust future upstream confidence.";
  return `Resolve missing trust signal: ${kind}.`;
}

function round(value: number) {
  return Math.round(value * 100) / 100;
}

function averageDimensionScore(review: DownstreamReview) {
  if (review.dimensions.length === 0) return 0;
  const total = review.dimensions.reduce((sum, dimension) => sum + clamp01(dimension.score), 0);
  return round(total / review.dimensions.length);
}

function clamp01(value: number) {
  return Math.max(0, Math.min(1, value));
}
