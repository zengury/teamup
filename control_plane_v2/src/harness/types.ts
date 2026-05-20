export type AgentName = "tangseng" | "bajie" | "houge" | "shaseng" | "bailongma";

export type AgentRunStatus =
  | "queued"
  | "building_context"
  | "running"
  | "waiting_for_approval"
  | "blocked"
  | "completed"
  | "failed";

export type ArtifactStatus = "draft" | "pending_approval" | "approved" | "rejected";

export type Artifact = {
  id: string;
  engagementId: string;
  kind: string;
  title: string;
  body: Record<string, unknown>;
  status: ArtifactStatus;
  createdByAgent?: AgentName;
  sourceArtifactIds: string[];
  createdAt: string;
};

export type AgentEvent = {
  type: string;
  engagementId: string;
  payload: Record<string, unknown>;
};

export type ApprovalRequest = {
  type: string;
  requestedFrom: "founder" | "customer" | "shaseng" | "tangseng";
  reason: string;
  artifactIds: string[];
};

export type ContextPacket = {
  engagementId: string;
  agentName: AgentName;
  triggerType: string;
  facts: string[];
  sourceArtifacts: Artifact[];
  workingNotes: string[];
};

export type ToolPolicy = {
  allowedTools: string[];
  blockedTools: string[];
  requiresApproval: string[];
};

export type ApprovalPolicy = {
  requiredForArtifactKinds: string[];
  requiredForEventTypes: string[];
};

export type MemoryPolicy = {
  includeClientProfile: boolean;
  includeRecentRuns: number;
  includeTranscriptSlices: boolean;
};

export type EvalPolicy = {
  runSchemaValidation: boolean;
  runShasengReview: boolean;
  maxRepairAttempts: number;
};

export type AgentOutput = {
  artifacts: Array<{
    kind: string;
    title: string;
    body: Record<string, unknown>;
    status?: ArtifactStatus;
  }>;
  events: Array<{
    type: string;
    payload: Record<string, unknown>;
  }>;
  approvalRequest?: Omit<ApprovalRequest, "artifactIds">;
};

export type AgentConfig = {
  name: AgentName;
  model: string;
  systemPrompt: string;
  outputSchema: OutputSchema;
  toolPolicy: ToolPolicy;
  approvalPolicy: ApprovalPolicy;
  memoryPolicy: MemoryPolicy;
  evalPolicy: EvalPolicy;
};

export type AgentRunRequest = {
  engagementId: string;
  agentName: AgentName;
  triggerType: string;
  triggerPayload: Record<string, unknown>;
  inputArtifactIds: string[];
};

export type AgentRunResult = {
  runId: string;
  status: AgentRunStatus;
  outputArtifactIds: string[];
  nextEvents: AgentEvent[];
  approvalRequest?: ApprovalRequest;
  error?: string;
};

export type OutputSchema = {
  requiredArtifactKinds: string[];
  allowedEventTypes: string[];
};

export type ModelAdapter = {
  complete(input: {
    model: string;
    systemPrompt: string;
    context: ContextPacket;
    triggerPayload: Record<string, unknown>;
  }): Promise<AgentOutput>;
};

export type HarnessStore = {
  createRun(input: {
    engagementId: string;
    agentName: AgentName;
    triggerType: string;
    model: string;
  }): Promise<{ id: string }>;
  updateRun(id: string, patch: Partial<AgentRunResult> & { status: AgentRunStatus }): Promise<void>;
  getArtifacts(ids: string[]): Promise<Artifact[]>;
  saveArtifact(artifact: Omit<Artifact, "id" | "createdAt">): Promise<Artifact>;
  saveApproval(runId: string, approval: ApprovalRequest): Promise<void>;
  emitEvent(event: AgentEvent): Promise<void>;
};
